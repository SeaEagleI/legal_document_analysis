import requests,json
import sqlite3
import os
import ujson
import re
def dump_data(data, path):
    ujson.dump(data, open(path, "w+", encoding="utf-8"), ensure_ascii=False, indent=4)

def db_to_txt(cursor, sql, path):
    """将sql查找的结果直接存为.txt文件
    """
    cursor.execute(sql)
    res = cursor.fetchall()
    tar = []
    if isinstance(res, list):
        for court_name, judge in res:
            court_name = re.sub(r"[^\u4e00-\u9fa5]", "", court_name)
            tar.append([court_name, judge])
        dump_data(tar, path)
    else:
        print("error")
        exit()
def json_to_txt(path, out_path):
    with open(path, 'r', encoding='utf-8') as json_file:
        load_dict = json.load(json_file)
        dump_data(list(load_dict.items()), out_path)
def get_location(address):
    key='556d58e40fb02e1450634b32d4034e3b'
    url='http://restapi.amap.com/v3/geocode/geo?key={}&address={}&output=json&callback=showLocation'.format(key,address)
    #http://restapi.amap.com/v3/geocode/geo?key=a5fd9e9b182aa165825474fa69c78d80&address=�������Ժ&output=json&callback=showLocation?
    res=requests.get(url)
    res=res.text
    res=res.strip('showLocation(')
    res=res.strip(')')

    dict=json.loads(res)
    return dict['geocodes'][0]['location']

def load_data(path):
    """将path记录的数据读取为列表
    """
    with open(path,"r", encoding='utf-8') as f:
        laws=f.read()
        laws=json.loads(laws)
    return laws

def gen_jsdata(name, flag, datasrc):
    """name只是需要存储的文件名，默认存在./data文件夹下
    flag 指示0热力图或者1热点图
    datasrc 是list文件[[法院名, 断案数],[] ...]
    """
    result="var heatmapData = ["
    for l in datasrc:
        # print(l)
        try:
            lo=get_location(l[0])
            lng,lat=lo.split(',')
            #sqll="select count(*) from document where s2='{}' ".format(l)
            #cursor.execute(sqll)
            #rr=cursor.fetchall()
            #count=0
            if flag == 0: # 热力图
                temp={"lng":float(lng),"lat":float(lat),"count":int(l[1])}
            else: # 热点图
                temp={"lng":float(lng),"lat":float(lat),"count":int(10)}
            # print(str(temp))
            result+=str(temp)
            result+=','
        except:
            print(1)
    result=result.strip(',')
    result+=']'
    path = f'./data/{name}'
    with open(path,"w") as f:
        f.write(result)

def gen_yearly_txt(start, end, cursor):
    """将[start,end]的数据，每一年分别存到当前目录下的txt文件里
    """
    sql = """
        select s2 as 法院名, count(*) as 案件数 from document
        where s31 like '%{}%'
        group by s2
    """
    for year in range(start, end + 1):
        path = "num_law_" + str(year) + ".txt"
        sql_yearly = sql.format(year)
        db_to_txt(cursor, sql_yearly, path)

def get_heatmap_yearly(start, end, name, path):
    for year in range(start, end + 1):
        yname = name.format(year)
        ypath = path.format(year)
        laws = load_data(ypath)
        gen_jsdata(yname, 0, laws)
def get_scatter(name, path):
    laws = load_data(path)
    gen_jsdata(name, 1, laws)
def get_heatmap(name, path):
    laws = load_data(path)
    gen_jsdata(name, 0, laws)
def js_to_html(src, out):
    """
    src: xxx.js
    out: xxx.html
    """
    with open("./pic/HeatMap_court.html", "r",encoding="utf-8") as src_file:
        src_lines = src_file.readlines()
        tar_lines = src_lines[:]
        tar_lines[19] = f"    <script type=\"text/javascript\" src=\"../data/{src}\"></script>\n"
        with open(f"./pic/{out}", "w",encoding="utf-8") as tar_file:
            tar_file.writelines(tar_lines)

def gen_heatmap_html(start, end):
    with open("./pic/HeatMap_court.html", "r",encoding="utf-8") as src:
        src_lines = src.readlines()
        for year in range(start, end + 1):
            tar_lines = src_lines[:]
            tar_lines[19] = "    <script type=\"text/javascript\" src=\"../data/court_judge_{}.js\"></script>\n".format(year)
            with open("./pic/HeatMap_court_{}.html".format(year), "w",encoding="utf-8") as tar:
                tar.writelines(tar_lines)


#print(get_location(address))
if __name__ == "__main__":

    name = "court_count"
    out = "all_court_loc.js"
    # path = os.path.join(os.path.dirname(__file__),f'../data/count/{name}.json')
    # json_to_txt(path, f"{name}.txt")
    # get_scatter(out, f"{name}.txt")
    # js_to_html(out, f'{name}.html')

    get_heatmap("all_court_count.js", f"{name}.txt")
    # db_path = os.path.join(os.path.dirname(__file__),'../data/judge.db')
    # conn = sqlite3.connect(db_path)
    # cursor = conn.cursor()
    #
    # get_scatter("court_loc.js", "num_law.txt")
    # # start = 2013
    # # end = 2021
    # # gen_yearly_txt(start, end, cursor)
    # # get_heatmap_yearly(start, end, "court_judge_{}.js.", "num_law_{}.txt")
    # # gen_heatmap_html(start, end)
    # cursor.close()
    # conn.close()