# -*- coding: UTF-8 -*-
import sqlite3
import os
# import matplotlib as mpl
#mpl.use('TkAgg')
import matplotlib.pyplot as plt
import json

plt.rcParams['font.sans-serif']=['SimHei'] #用来正常显示中文标签
plt.rcParams['axes.unicode_minus'] = False #用来正常显示负号
######################
### 辅助函数       ###
######################
def search(cursor, sql, start, num):
    """查询满足sql条件的记录，从start开始，共num条
    返回一个列表，每一行是一个需要的记录
    """
    limit = f" limit {num} offset {start};"
    sql += limit
    cursor.execute(sql)
    res = cursor.fetchall()
    return res

def anlysis_one_seg(field_count, cursor, sql, start, num, end = float('inf')):
    """对一个字段进行次数统计，例如每年的案件数目
    """
    ret = ["no meaning"]
    while ret and start < end:
        ret = search(cursor, sql, start, num)
        for record in ret:
            field = record[0]
            if field not in field_count:
                field_count[field] = 0
            else:
                field_count[field] += 1
        start += num

def draw_picture(keyword_dict, xlabel = "", ylabel = "", title = "", key = 1):
    def auto_text(rects):
        for rect in rects:
            plt.text(rect.get_x(), rect.get_height(), rect.get_height(), ha='left', va='bottom')

    keyword_dict={k: v for k, v in sorted(keyword_dict.items(), key=lambda item: item[key], reverse = True)}
    X_key=list(keyword_dict.keys())
    Y_key=list(keyword_dict.values())

    new_X_key = []
    for word in X_key:
        if len(word) > 10 and title == '全国各省判案数':
            word = '新疆建设兵团'
        single = ""
        for char in word:
            single = single + char + "\n"
        new_X_key.append(single)
    X_key = new_X_key

    # plt.barh(X_key, Y_key, 0.4, color="green")
    rects = plt.bar(X_key, Y_key, 0.4, color="green")
    ax = plt.gca()
    ax.yaxis.get_offset_text().set(size=20)
    plt.xlabel(xlabel, fontsize = 18)
    plt.xticks(fontsize = 15)
    plt.ylabel(ylabel, fontsize = 18)
    plt.yticks(fontsize = 15)
    plt.title(title, fontsize = 20)
    plt.grid()
    plt.tight_layout()

    # auto_text(rects)
    plt.show()
    plt.savefig(title + "_chart.jpg")

def search_all(cursor, sql):
    cursor.execute(sql)
    res = cursor.fetchall()
    return res
def analysis(cursor, sql, dict):
    ret = search_all(cursor, sql)
    for record in ret:
        dict[record[1]] = record[0]
    return dict

######################
### 每一年的案件数 ###
######################
def analysis_by_year(cursor, title):
    sql_year = """select substr(s31, 0, 5) as 年份, count(*) as 案件数 from document
group by 年份;"""
    start, num = 0, 100
    year_count = {}
    res = search_all(cursor, sql_year)
    for record in res:
        year_count[record[0]] = record[1]
    draw_picture(year_count, xlabel=u"年份", ylabel=u"案件数", title=title)
######################
### 法院的案件数   ###
######################

## 分类参考：
## https://zh-cn.chinajusticeobserver.com/a/magnificent-four-level-pyramid-chinas-court-system
def analysis_by_court(cursor, title):
    sql_court = """
    select count(*) 数量,
case
    when s2 like '%最高人民法院%' then '最高人民法院'
    when s2 like '%高级人民法院%' then '高级人民法院'
    when s2 like '%中级人民法院%' then '中级人民法院'
    when s2 like '%区%人民法院%' then '区人民法院'
    when s2 like '%县%人民法院%' then '县人民法院'
    when s2 like '%市%人民法院%' then '市人民法院'
    when s2 like '%省%人民法院%' then '省人民法院'
    when s2 like '%知识产权法院%' then '知识产权法院'
    when s2 like '%互联网法院%' then '互联网法院'
    when s2 like '%海事法院%' then '海事法院'
    when s2 like '%铁路运输%法院%' then '铁路运输法院'
    else '未知类别'
end 法院类别
from document
group by 法院类别
    """
    ret = search_all(cursor, sql_court)
    court_count = {}

    for record in ret:
        court_count[record[1]] = record[0]
    draw_picture(court_count, xlabel=u"法院", ylabel=u"案件数", title=title, key=1)

def analysis_by_province(cursor, title):
    sql_pro = """
    select count(*) 数量,
case
    when s2 like '%最高%' or s22 like '%最高%' or s7 like '% 最高法%' then '最高人民法院'
    when s2 like '%河北%' or s22 like '%河北%' or s7 like '%冀%' then '河北省'
    when s2 like '%山西%' or s22 like '%山西%' or s7 like '%晋%' then '山西省'
    when s2 like '%辽宁%' or s22 like '%辽宁%' or s7 like '%辽%' then '辽宁省'
    when s2 like '%吉林%' or s22 like '%吉林%' or s7 like '%吉%' then '吉林省'
    when s2 like '%黑龙江%' or s22 like '%黑龙江%' or s7 like '%黑%' then '黑龙江省'
    when s2 like '%江苏%' or s22 like '%江苏%' or s7 like '%苏%' then '江苏省'
    when s2 like '%浙江%' or s22 like '%浙江%' or s7 like '%浙%' then '浙江省'
    when s2 like '%安徽%' or s22 like '%安徽%' or s7 like '%皖%' then '安徽省'
    when s2 like '%福建%' or s22 like '%福建%' or s7 like '%闽%' then '福建省'
    when s2 like '%江西%' or s22 like '%江西%' or s7 like '%赣%' then '江西省'
    when s2 like '%山东%' or s22 like '%山东%' or s7 like '%鲁%' then '山东省'
    when s2 like '%河南%' or s22 like '%河南%' or s7 like '%豫%' then '河南省'
    when s2 like '%湖北%' or s22 like '%湖北%' or s7 like '%鄂%' then '湖北省'
    when s2 like '%湖南%' or s22 like '%湖南%' or s7 like '%湘%' then '湖南省'
    when s2 like '%广东%' or s22 like '%广东%' or s7 like '%粤%' then '广东省'
    when s2 like '%海南%' or s22 like '%海南%' or s7 like '%琼%' then '海南省'
    when s2 like '%四川%' or s22 like '%四川%' or s7 like '%川%' then '四川省'
    when s2 like '%贵州%' or s22 like '%贵州%' or s7 like '%贵%' then '贵州省'
    when s2 like '%云南%' or s22 like '%云南%' or s7 like '%云%' then '云南省'
    when s2 like '%陕西%' or s22 like '%陕西%' or s7 like '%陕%' then '陕西省'
    when s2 like '%甘肃%' or s22 like '%甘肃%' or s7 like '%甘%' then '甘肃省'
    when s2 like '%青海%' or s22 like '%青海%' or s7 like '%青%' then '青海省'
    when s2 like '%台湾%' or s22 like '%台湾%' or s7 like '%台%' then '台湾省'
    when s2 like '%内蒙%' or s22 like '%内蒙%' or s7 like '%蒙%' then '内蒙古自治区'
    when s2 like '%广西%' or s22 like '%广西%' or s7 like '%桂%' then '广西壮族自治区'
    when s2 like '%西藏%' or s22 like '%西藏%' or s7 like '%藏%' then '西藏自治区'
    when s2 like '%宁夏%' or s22 like '%宁夏%' or s7 like '%宁%' then '宁夏回族自治区'
    when s2 like '%新疆%' or s22 like '%新疆%' or s7 like '%新%' then '新疆维吾尔自治区'
    when s2 like '%北京%' or s22 like '%北京%' or s7 like '%京%' then '北京市'
    when s2 like '%天津%' or s22 like '%天津%' or s7 like '%津%' then '天津市'
    when s2 like '%上海%' or s22 like '%上海%' or s7 like '%沪%' then '上海市'
    when s2 like '%重庆%' or s22 like '%重庆%' or s7 like '%渝%' then '重庆市'
    else '未知类别'
end 省份
from document
group by 省份
order by 数量;
    """
    pro_count = {}
    pro_count = analysis(cursor, sql_pro, pro_count)
    draw_picture(pro_count, xlabel=u"省份", ylabel=u"案件数", title=title, key=1)

def analysis_by_type(cursor, title):
    sql_type = """
    select count(*) 数量, s11 案由 from document
    group by 案由
    having 数量 > 200;
    """
    type_count = {}
    type_count = analysis(cursor, sql_type, type_count)
    draw_picture(type_count, xlabel=u"类别", ylabel=u"案件数", title=title, key=1)

def total_judge(cursor):
    sql = "select count(*) from document;"
    ret = search_all(cursor, sql)
    return ret

##############################
### 直接来源于json的分析   ###
##############################
def load_and_draw(path, xlabel, ylabel, title):

    with open(path, 'r', encoding='utf-8') as json_file:
        load_dict = json.load(json_file)
        print(load_dict)
        draw_picture(load_dict, xlabel, ylabel, title)

if __name__ == "__main__":
    # name = "judge"
    # db_path = os.path.join(os.path.dirname(__file__),f'../data/{name}.db')
    # conn = sqlite3.connect(db_path)
    # cursor = conn.cursor()


    # analysis_by_year(cursor, name + "每年案件数")
    # analysis_by_court(cursor, name + "法院类别案件数")
    # analysis_by_province(cursor, name + "每省案件数")
    # analysis_by_type(cursor, name + "每类案件数")

    # cursor.close()
    # conn.close()
    names = ['case_type_count', 'charge_type_count', 'court_level_count', 'doc_type_count', 'keyword_count', 'province_count', 'year_count']
    xlabels = ['案件类型', '案由类型', '法院层级', '文书类型', '关键词', '省份', '年份']
    ylabels = ['数量'] * 7
    titles = ['全国各案件类型判案数', '全国各案由判案数', '全国各级法院判案数', '各文书类型判案数', '高频关键词频率统计', '全国各省判案数', '全国每年度判案数']
    for name, xlabel, ylabel, title in zip(names, xlabels, ylabels, titles):
        path = os.path.join(os.path.dirname(__file__),f'../data/count/{name}.json')
        load_and_draw(path, xlabel, ylabel, title)

