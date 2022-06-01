# -*- coding: utf-8 -*-
import sqlite3

from bs4 import BeautifulSoup

'''
数据库：
- document
  包含绝大部分信息：
  ('doc_id', 'fulltext', 's1', 's2', 's3', 's6', 's7', 's8', 's9', 's31', 's41', 's43', 's22', 's23', 's25', 's26', 's27', 's28', 's11', 'viewCount')
  不包含：
  (s17当事人列表) (s47法律条款列表) 这两个用关系表存储；s45, wenshuAy, relWenshu舍弃;
  特殊：
  (s11案由) 虽然是列表，目前没发现多个的情况，用s11[0]替代，依然保存在document表中
  s5重命名doc_id并充当主键, qwContent重命名为fulltext，主键类型是text，但其他表的主键都是自增的integer
  
- party
  ('id', 'name')
- party_document_rel
  ('id', 'party_id', 'doc_id')
- law
  ('id', 'name', 'clause')
- law_document-rel
  ('id', 'law_id', 'doc_id')
'''
def db_init():
    conn = sqlite3.connect('judge.db')
    cursor = conn.cursor()
    cursor.execute('''
    create table document
    (
        doc_id   text
            constraint document_pk
                primary key,
        fulltext text,
        s1       text,
        s2       text,
        s3       text,
        s6       text,
        s7       text,
        s8       text,
        s9       text,
        s31      text,
        s41      text,
        s43      text,
        s22      text,
        s23      text,
        s25      text,
        s26      text,
        s27      text,
        s28      text,
        s11      text,
        view_count text
    );
    ''')
    cursor.execute('''
    create table party
    (
        id integer
            constraint party_pk
                primary key autoincrement,
        name text
    );
    ''')
    cursor.execute('''
    create table party_document_rel
    (
        id integer
            constraint party_document_rel_pk
                primary key autoincrement,
        party_id integer,
        doc_id text
    );
    ''')
    cursor.execute('''
    create table law
    (
        id integer
            constraint law_pk
                primary key autoincrement,
        name text,
        clause text
    );
    ''')
    cursor.execute('''
    create table "law_document_rel"
    (
        id integer
            constraint "law_document-rel_pk"
                primary key autoincrement,
        law_id integer,
        doc_id text
    );
    ''')
    conn.commit()
    cursor.close()
    conn.close()


# 插入document表
def add_doc(res, cursor):
    # 允许存入document表的key
    allow_keys = ['s5', 'qwContent', 's1', 's2', 's3', 's6', 's7', 's8', 's9', 's31', 's41', 's43', 's22', 's23', 's25', 's26', 's27', 's28', 's11', 'viewCount']
    # s11数组变字段
    if 's11' in res:
        res['s11'] = res['s11'][0]
    # 补全
    for key in allow_keys:
        if key not in res:
            res[key] = ''
    # 将全文由html转换成文本
    soup = BeautifulSoup(res['qwContent'], 'html.parser')
    res['qwContent'] = soup.get_text()
    # 拼接sql
    field_str = ""
    parma_str = ""
    mapping_list = []
    for key in allow_keys:
        if key == 's5':
            key = 'doc_id'
        if key == 'qwContent':
            key = 'fulltext'
        if key == 'viewCount':
            key = 'view_count'
        field_str += key + ', '
    for key in allow_keys:
        parma_str += '?, '
    for key in allow_keys:
        mapping_list.append(res[key])
    field_str = field_str[0:-2]
    parma_str = parma_str[0:-2]
    doc_sql = 'insert into document (' + field_str + ') values (' + parma_str + ')'
    print(doc_sql)
    cursor.execute(doc_sql, tuple(mapping_list))
    print('插入' + str(cursor.rowcount) + '条数据')


# 插入party当事人表
def add_party(res, cursor):
    party_sql = "insert into party (name) values (?)"
    rel_sql = "insert into party_document_rel (party_id, doc_id) values (?, ?)"
    for name in res['s17']:
        print(party_sql, name)
        cursor.execute(party_sql, (name,))
        party_id = cursor.lastrowid
        cursor.execute(rel_sql, (party_id, res['s5']))


# 插入law法律条款表
def add_law(res, cursor):
    law_sql = "insert into law (name, clause) values (?, ?)"
    rel_sql = "insert into law_document_rel (law_id, doc_id) values (?, ?)"
    for d in res['s47']:
        cursor.execute(law_sql, (d['fgmc'], d['tkx']))
        law_id = cursor.lastrowid
        cursor.execute(rel_sql, (law_id, res['s5']))


def add(res):
    conn = sqlite3.connect('judge.db')
    cursor = conn.cursor()
    add_doc(res, cursor)
    add_party(res, cursor)
    add_law(res, cursor)
    conn.commit()
    cursor.close()
    conn.close()


if __name__ == '__main__':
    res = {
    "s1": "北京盈拓文化传媒有限公司等与国家知识产权局二审行政判决书",
    "s2": "北京市高级人民法院",
    "s3": "100",
    "s5": "959d63e24f2e42828c24ad4a000b2600",
    "s6": "01",
    "s7": "（2021）京行终963号",
    "s8": "行政案件",
    "s9": "行政二审",
    "s31": "2021-06-09",
    "s41": "2021-06-17",
    "s43": "01",
    "s22": "北京市高级人民法院\n行政判决书\n（2021）京行终963号",
    "s23": "上诉人北京盈拓文化传媒有限公司（简称盈拓公司）因商标权无效宣告请求行政纠纷一案，不服北京知识产权法院（2019）京73行初4301号行政判决，向本院提起上诉。本院于2021年3月11日受理后，依法组成合议庭进行了审理。本案现已审理终结",
    "s25": "北京知识产权法院查明：\n一、诉争商标\n1．注册人：盈拓公司。\n2．注册号：20680746。\n3．申请日期：2016年7月18日。\n4．专用期限至：2027年9月13日。\n5．标志：\n6．核定使用服务（第41类，类似群：4102；4105）：4102：组织文化或教育展览、组织表演（演出）、安排和组织音乐会；娱乐信息、演出、提供在线录像（非下载）、演出制作、演出座位预定、票务代理服务（娱乐）、现场表演。\n二、云智联网络科技（北京）有限公司（简称云智联公司）主张在先使用的商标\n1．注册情况：未注册。\n2．标志：超级星饭团。\n三、被诉裁定：商评字［2019］第22893号《关于第20680746号“超级星饭团”商标无效宣告请求裁定书》。\n被诉裁定作出时间：2019年1月29日。\n原国家工商行政管理总局商标评审委员会（简称商标评审委员会）认定：云智联公司提交的证据2、4、5、6显示“超级星饭团”商标在第41类娱乐信息等服务上在先使用并已有一定知名度。盈拓公司作为同行业者，对此理应知晓。证据1显示云智联公司为“超级星饭团”现在使用主体，且盈拓公司未提交证据证明云智联公司使用过其他微博名称，或者在先另有他人使用“超级星饭团”。诉争商标核定使用的“组织表演（演出）、娱乐服务、演出”等服务与云智联公司在先使用的“娱乐信息”等服务类似，其文字构成完全相同，故诉争商标的注册已构成2013年修正的《中华人民共和国商标法》（简称2013年商标法）第三十二条“以不正当手段抢先注册他人已经使用并有一定影响的商标”所指情形。商标评审委员会裁定：诉争商标予以无效宣告。\n四、其他事实\n2018年4月4日，云智联公司向商标评审委员会申请宣告诉争商标无效，并提交了以下主要证据：\n1．“超级星饭团”微博首页截图；\n2．云智联公司于诉争商标申请日之前在新浪微博发布的微博截屏；\n3．“超级星饭团”宣传使用视频；\n4．“超级星饭团”ａｐｐ在知名应用平台的后台、软件下载页面、评论页面截屏；\n5．ＡＯＳ100移动推广数据平台关于“超级星饭团”ａｐｐ的版本记录、安卓端下载量等的截屏；\n6．云智联公司与知名影视演员、著名视频网站爱奇艺合作的微博；\n7．云智联公司以“超级星饭团”名义赞助的电视剧片头和片尾的截图；\n8．盈拓公司“唯票”软件使用信息；\n9．盈拓公司的ＩＣＰ备案信息查询结果截屏；\n10．盈拓公司申请注册商标列表；\n11．其他证据材料。\n盈拓公司向商标评审委员会提交了以下主要证据：\n1．诉争商标词汇说明；\n2．部分合同复印件；\n3．盈拓公司使用诉争商标的证据。\n盈拓公司不服被诉裁定，于法定期限向北京知识产权法院提起行政诉讼。\n在原审诉讼中，盈拓公司补充提交超级星饭团微信公众号娱乐信息截图作为证据。云智联公司补充提交以下证据：\n1．云智联公司“超级星饭团”于2017年、2018年广告投放合同；\n2．媒体微信公众号文章；\n3．截图。\n北京知识产权法院认为：云智联公司提交的证据能够证明云智联公司在诉争商标申请注册日前已经在娱乐信息等服务上使用了“超级星饭团”商标，已为相关公众所知晓并具有一定的影响力。诉争商标核定使用的“组织表演（演出）、娱乐服务、演出”等服务与云智联公司“超级星饭团”商标所使用的“娱乐信息”等服务关联性较大，属于类似服务。盈拓公司与云智联公司为同行业经营者，对云智联公司“超级星饭团”商标理应知晓，其在注册商标时亦应负有较高的注意义务。因此，诉争商标在“组织表演（演出）、娱乐服务、演出”等服务上的注册，已构成2013年商标法第三十二条关于“以不正当手段抢先注册他人已经使用并有一定影响的商标”之情形。\n综上，北京知识产权法院依照《中华人民共和国行政诉讼法》第六十九条之规定，判决：驳回盈拓公司的诉讼请求。\n盈拓公司不服原审判决，向本院提起上诉，请求撤销原审判决及被诉裁定，判令国家知识产权局重新作出裁定，其主要上诉理由为：一、云智联公司提交的证据2、4、5、6不足以证明在诉争商标申请日前，其对“超级星饭团”的使用属于商标性使用，亦不足以证明其对“超级星饭团”构成在先使用并具有一定影响。二、云智联公司提交的证据1与云智联公司并无关联性，不能证明在第41类服务上使用了“超级星饭团”商标，更无法证明其在微博中使用的“超级星饭团”具有知名度和影响力。因此，诉争商标的注册并未违反2013年商标法第三十二条的相关规定。\n国家知识产权局、云智联公司服从原审判决。\n经审理查明：原审法院查明的事实属实，且有诉争商标档案、被诉裁定、各方当事人在行政程序和诉讼程序中提交的证据及当事人陈述等在案佐证，本院予以确认。\n另查，根据中央机构改革部署，原国家工商行政管理总局商标局、商标评审委员会的相关职责由国家知识产权局统一行使",
    "s26": "本院认为：\n2013年商标法第三十二条规定，申请商标注册不得损害他人现有的在先权利，也不得以不正当手段抢先注册他人已经使用并有一定影响的商标。\n“不得以不正当手段抢先注册他人在先使用并具有一定影响的商标”的规定，旨在规制抢注他人使用在先并有一定影响的商标的行为。认定诉争商标是否违反上述规定，应同时具备下列情形：1．未注册商标在诉争商标申请日之前已经使用并有一定影响；2．诉争商标与在先使用的未注册商标构成相同或近似商标；3．诉争商标指定使用的商品与在先使用的未注册商标所使用的商品构成相同或者类似商品；4．诉争商标申请人明知或者应知他人在先使用商标。\n本案中，云智联公司提交的证据能够证明其在诉争商标申请注册之前已经在“娱乐信息”等服务上使用了“超级星饭团”商标。云智联公司提交的新浪微博发布的微博截屏，“超级星饭团”ａｐｐ在知名应用平台的后台、软件下载页面、评论页面截屏，ＡＯＳ100移动推广数据平台关于“超级星饭团”ａｐｐ的版本记录、安卓端下载量等的截屏，云智联公司与影视演员、爱奇艺合作的微博等证据可以证明，云智联公司“超级星饭团”商标经过持续使用和宣传，已为相关公众所知晓并具有一定的影响。诉争商标与云智联公司在先使用的“超级星饭团”标志完全相同。同时，诉争商标核定使用的“组织表演（演出）、娱乐服务、演出”等服务与云智联公司“超级星饭团”商标所使用的“娱乐信息”等服务密切关联。另外，盈拓公司与云智联公司为同行业经营者，对云智联公司在先使用的“超级星饭团”商标理应知晓，但盈拓公司未尽合理避让义务，在类似服务上申请注册标志相同的商标，其行为难谓正当。因此，诉争商标在核定使用服务上的注册构成2013年商标法第三十二条规定的“不得以不正当手段抢先注册他人已经使用并有一定影响的商标”情形。原审判决及被诉裁定的对此认定并无不当，本院予以维持。盈拓公司的相关上诉理由缺乏事实和法律依据，本院不予支持。\n综上所述，原审判决认定事实清楚，适用法律正确，程序合法，应予维持。盈拓公司的上诉理由不能成立，对其上诉请求，本院不予支持。依据《中华人民共和国行政诉讼法》第八十九条第一款第一项之规定，判决如下",
    "s27": "驳回上诉，维持原判。\n一、二审案件受理费各一百元，均由北京盈拓文化传媒有限公司负担（均已交纳）。\n本判决为终审判决",
    "s28": "审判长孔庆兵\n审判员孙柱永\n审判员刘岭\n二〇二一年六月九日\n法官助理何娟\n书记员郭媛媛",
    "s17": [
        "北京盈拓文化传媒有限公司",
        "云智联网络科技（北京）有限公司",
        "国家知识产权局"
    ],
    "s45": [
        "在先权利",
        "近似商标",
        "类似商品",
        "程序合法"
    ],
    "s11": [
        "其他行政行为"
    ],
    "wenshuAy": [
        {
            "key": "s13",
            "value": "xz255",
            "text": "其他行政行为"
        }
    ],
    "s47": [
        {
            "tkx": "第八十九条第一款第一项",
            "fgmc": "《中华人民共和国行政诉讼法（2017修正）》",
            "fgid": "3779247"
        }
    ],
    "relWenshu": [],
    "qwContent": "<!DOCTYPE HTML PUBLIC -//W3C//DTD HTML 4.0 Transitional//EN'><HTML><HEAD><TITLE></TITLE></HEAD><BODY><div style='TEXT-ALIGN: center; LINE-HEIGHT: 25pt; MARGIN: 0.5pt 0cm; FONT-FAMILY: 黑体; FONT-SIZE: 18pt;'>北京市高级人民法院</div><div style='TEXT-ALIGN: center; LINE-HEIGHT: 25pt; MARGIN: 0.5pt 0cm; FONT-FAMILY: 黑体; FONT-SIZE: 18pt;'>行 政 判 决 书</div><div id='1'  style='TEXT-ALIGN: right; LINE-HEIGHT: 25pt; MARGIN: 0.5pt 0cm;  FONT-FAMILY: 宋体;FONT-SIZE: 15pt; '>（2021）京行终963号</div><div id='2'  style='LINE-HEIGHT: 25pt; TEXT-INDENT: 30pt; MARGIN: 0.5pt 0cm;FONT-FAMILY: 宋体; FONT-SIZE: 15pt;'>上诉人（原审原告）：北京盈拓文化传媒有限公司，住所地北京市海淀区。</div><div style='LINE-HEIGHT: 25pt; TEXT-INDENT: 30pt; MARGIN: 0.5pt 0cm;FONT-FAMILY: 宋体; FONT-SIZE: 15pt;'>法定代表人：李伟东，经理。</div><div style='LINE-HEIGHT: 25pt; TEXT-INDENT: 30pt; MARGIN: 0.5pt 0cm;FONT-FAMILY: 宋体; FONT-SIZE: 15pt;'>委托诉讼代理人：张颖，北京云亭律师事务所律师。</div><div style='LINE-HEIGHT: 25pt; TEXT-INDENT: 30pt; MARGIN: 0.5pt 0cm;FONT-FAMILY: 宋体; FONT-SIZE: 15pt;'>委托诉讼代理人：胡明昕，北京云亭律师事务所实习律师，住天津市河西区。</div><div style='LINE-HEIGHT: 25pt; TEXT-INDENT: 30pt; MARGIN: 0.5pt 0cm;FONT-FAMILY: 宋体; FONT-SIZE: 15pt;'>被上诉人（原审被告）：国家知识产权局，住所地北京市海淀区。</div><div style='LINE-HEIGHT: 25pt; TEXT-INDENT: 30pt; MARGIN: 0.5pt 0cm;FONT-FAMILY: 宋体; FONT-SIZE: 15pt;'>法定代表人：申长雨，局长。</div><div style='LINE-HEIGHT: 25pt; TEXT-INDENT: 30pt; MARGIN: 0.5pt 0cm;FONT-FAMILY: 宋体; FONT-SIZE: 15pt;'>委托诉讼代理人：赵晶晶，国家知识产权局审查员。</div><div style='LINE-HEIGHT: 25pt; TEXT-INDENT: 30pt; MARGIN: 0.5pt 0cm;FONT-FAMILY: 宋体; FONT-SIZE: 15pt;'>原审第三人：云智联网络科技（北京）有限公司，住所地北京市朝阳区。</div><div style='LINE-HEIGHT: 25pt; TEXT-INDENT: 30pt; MARGIN: 0.5pt 0cm;FONT-FAMILY: 宋体; FONT-SIZE: 15pt;'>法定代表人：欧阳云，董事长。</div><div style='LINE-HEIGHT: 25pt; TEXT-INDENT: 30pt; MARGIN: 0.5pt 0cm;FONT-FAMILY: 宋体; FONT-SIZE: 15pt;'>委托诉讼代理人：刘乐昕，云智联网络科技（北京）有限公司员工，住北京市朝阳区。</div><div id='2'  style='LINE-HEIGHT: 25pt; TEXT-INDENT: 30pt; MARGIN: 0.5pt 0cm;FONT-FAMILY: 宋体; FONT-SIZE: 15pt;'>上诉人北京盈拓文化传媒有限公司（简称盈拓公司）因商标权无效宣告请求行政纠纷一案，不服北京知识产权法院（2019）京73行初4301号行政判决，向本院提起上诉。本院于2021年3月11日受理后，依法组成合议庭进行了审理。本案现已审理终结。</div><div style='LINE-HEIGHT: 25pt; TEXT-INDENT: 30pt; MARGIN: 0.5pt 0cm;FONT-FAMILY: 宋体; FONT-SIZE: 15pt;'>北京知识产权法院查明：</div><div style='LINE-HEIGHT: 25pt; TEXT-INDENT: 30pt; MARGIN: 0.5pt 0cm;FONT-FAMILY: 宋体; FONT-SIZE: 15pt;'>一、诉争商标</div><div style='LINE-HEIGHT: 25pt; TEXT-INDENT: 30pt; MARGIN: 0.5pt 0cm;FONT-FAMILY: 宋体; FONT-SIZE: 15pt;'>1．注册人：盈拓公司。</div><div style='LINE-HEIGHT: 25pt; TEXT-INDENT: 30pt; MARGIN: 0.5pt 0cm;FONT-FAMILY: 宋体; FONT-SIZE: 15pt;'>2．注册号：20680746。</div><div style='LINE-HEIGHT: 25pt; TEXT-INDENT: 30pt; MARGIN: 0.5pt 0cm;FONT-FAMILY: 宋体; FONT-SIZE: 15pt;'>3．申请日期：2016年7月18日。</div><div style='LINE-HEIGHT: 25pt; TEXT-INDENT: 30pt; MARGIN: 0.5pt 0cm;FONT-FAMILY: 宋体; FONT-SIZE: 15pt;'>4．专用期限至：2027年9月13日。</div><div style='LINE-HEIGHT: 25pt; TEXT-INDENT: 30pt; MARGIN: 0.5pt 0cm;FONT-FAMILY: 宋体; FONT-SIZE: 15pt;'>5．标志：</div><div style='LINE-HEIGHT: 25pt; TEXT-INDENT: 30pt; MARGIN: 0.5pt 0cm;FONT-FAMILY: 宋体; FONT-SIZE: 15pt;'>6．核定使用服务（第41类，类似群：4102；4105）：4102：组织文化或教育展览、组织表演（演出）、安排和组织音乐会；娱乐信息、演出、提供在线录像（非下载）、演出制作、演出座位预定、票务代理服务（娱乐）、现场表演。</div><div style='LINE-HEIGHT: 25pt; TEXT-INDENT: 30pt; MARGIN: 0.5pt 0cm;FONT-FAMILY: 宋体; FONT-SIZE: 15pt;'>二、云智联网络科技（北京）有限公司（简称云智联公司）主张在先使用的商标</div><div style='LINE-HEIGHT: 25pt; TEXT-INDENT: 30pt; MARGIN: 0.5pt 0cm;FONT-FAMILY: 宋体; FONT-SIZE: 15pt;'>1．注册情况：未注册。</div><div style='LINE-HEIGHT: 25pt; TEXT-INDENT: 30pt; MARGIN: 0.5pt 0cm;FONT-FAMILY: 宋体; FONT-SIZE: 15pt;'>2．标志：超级星饭团。</div><div style='LINE-HEIGHT: 25pt; TEXT-INDENT: 30pt; MARGIN: 0.5pt 0cm;FONT-FAMILY: 宋体; FONT-SIZE: 15pt;'>三、被诉裁定：商评字[2019]第22893号《关于第20680746号“超级星饭团”商标无效宣告请求裁定书》。</div><div style='LINE-HEIGHT: 25pt; TEXT-INDENT: 30pt; MARGIN: 0.5pt 0cm;FONT-FAMILY: 宋体; FONT-SIZE: 15pt;'>被诉裁定作出时间：2019年1月29日。</div><div style='LINE-HEIGHT: 25pt; TEXT-INDENT: 30pt; MARGIN: 0.5pt 0cm;FONT-FAMILY: 宋体; FONT-SIZE: 15pt;'>原国家工商行政管理总局商标评审委员会（简称商标评审委员会）认定：云智联公司提交的证据2、4、5、6显示“超级星饭团”商标在第41类娱乐信息等服务上在先使用并已有一定知名度。盈拓公司作为同行业者，对此理应知晓。证据1显示云智联公司为“超级星饭团”现在使用主体，且盈拓公司未提交证据证明云智联公司使用过其他微博名称，或者在先另有他人使用“超级星饭团”。诉争商标核定使用的“组织表演（演出）、娱乐服务、演出”等服务与云智联公司在先使用的“娱乐信息”等服务类似，其文字构成完全相同，故诉争商标的注册已构成2013年修正的《中华人民共和国商标法》（简称2013年商标法）第三十二条“以不正当手段抢先注册他人已经使用并有一定影响的商标”所指情形。商标评审委员会裁定：诉争商标予以无效宣告。</div><div style='LINE-HEIGHT: 25pt; TEXT-INDENT: 30pt; MARGIN: 0.5pt 0cm;FONT-FAMILY: 宋体; FONT-SIZE: 15pt;'>四、其他事实</div><div style='LINE-HEIGHT: 25pt; TEXT-INDENT: 30pt; MARGIN: 0.5pt 0cm;FONT-FAMILY: 宋体; FONT-SIZE: 15pt;'>2018年4月4日，云智联公司向商标评审委员会申请宣告诉争商标无效，并提交了以下主要证据：</div><div style='LINE-HEIGHT: 25pt; TEXT-INDENT: 30pt; MARGIN: 0.5pt 0cm;FONT-FAMILY: 宋体; FONT-SIZE: 15pt;'>1．“超级星饭团”微博首页截图；</div><div style='LINE-HEIGHT: 25pt; TEXT-INDENT: 30pt; MARGIN: 0.5pt 0cm;FONT-FAMILY: 宋体; FONT-SIZE: 15pt;'>2．云智联公司于诉争商标申请日之前在新浪微博发布的微博截屏；</div><div style='LINE-HEIGHT: 25pt; TEXT-INDENT: 30pt; MARGIN: 0.5pt 0cm;FONT-FAMILY: 宋体; FONT-SIZE: 15pt;'>3．“超级星饭团”宣传使用视频；</div><div style='LINE-HEIGHT: 25pt; TEXT-INDENT: 30pt; MARGIN: 0.5pt 0cm;FONT-FAMILY: 宋体; FONT-SIZE: 15pt;'>4．“超级星饭团”app在知名应用平台的后台、软件下载页面、评论页面截屏；</div><div style='LINE-HEIGHT: 25pt; TEXT-INDENT: 30pt; MARGIN: 0.5pt 0cm;FONT-FAMILY: 宋体; FONT-SIZE: 15pt;'>5．AOS100移动推广数据平台关于“超级星饭团”app的版本记录、安卓端下载量等的截屏；</div><div style='LINE-HEIGHT: 25pt; TEXT-INDENT: 30pt; MARGIN: 0.5pt 0cm;FONT-FAMILY: 宋体; FONT-SIZE: 15pt;'>6．云智联公司与知名影视演员、著名视频网站爱奇艺合作的微博；</div><div style='LINE-HEIGHT: 25pt; TEXT-INDENT: 30pt; MARGIN: 0.5pt 0cm;FONT-FAMILY: 宋体; FONT-SIZE: 15pt;'>7．云智联公司以“超级星饭团”名义赞助的电视剧片头和片尾的截图；</div><div style='LINE-HEIGHT: 25pt; TEXT-INDENT: 30pt; MARGIN: 0.5pt 0cm;FONT-FAMILY: 宋体; FONT-SIZE: 15pt;'>8．盈拓公司“唯票”软件使用信息；</div><div style='LINE-HEIGHT: 25pt; TEXT-INDENT: 30pt; MARGIN: 0.5pt 0cm;FONT-FAMILY: 宋体; FONT-SIZE: 15pt;'>9．盈拓公司的ICP备案信息查询结果截屏；</div><div style='LINE-HEIGHT: 25pt; TEXT-INDENT: 30pt; MARGIN: 0.5pt 0cm;FONT-FAMILY: 宋体; FONT-SIZE: 15pt;'>10．盈拓公司申请注册商标列表；</div><div style='LINE-HEIGHT: 25pt; TEXT-INDENT: 30pt; MARGIN: 0.5pt 0cm;FONT-FAMILY: 宋体; FONT-SIZE: 15pt;'>11．其他证据材料。</div><div style='LINE-HEIGHT: 25pt; TEXT-INDENT: 30pt; MARGIN: 0.5pt 0cm;FONT-FAMILY: 宋体; FONT-SIZE: 15pt;'>盈拓公司向商标评审委员会提交了以下主要证据：</div><div style='LINE-HEIGHT: 25pt; TEXT-INDENT: 30pt; MARGIN: 0.5pt 0cm;FONT-FAMILY: 宋体; FONT-SIZE: 15pt;'>1．诉争商标词汇说明；</div><div style='LINE-HEIGHT: 25pt; TEXT-INDENT: 30pt; MARGIN: 0.5pt 0cm;FONT-FAMILY: 宋体; FONT-SIZE: 15pt;'>2．部分合同复印件；</div><div style='LINE-HEIGHT: 25pt; TEXT-INDENT: 30pt; MARGIN: 0.5pt 0cm;FONT-FAMILY: 宋体; FONT-SIZE: 15pt;'>3．盈拓公司使用诉争商标的证据。</div><div style='LINE-HEIGHT: 25pt; TEXT-INDENT: 30pt; MARGIN: 0.5pt 0cm;FONT-FAMILY: 宋体; FONT-SIZE: 15pt;'>盈拓公司不服被诉裁定，于法定期限向北京知识产权法院提起行政诉讼。</div><div style='LINE-HEIGHT: 25pt; TEXT-INDENT: 30pt; MARGIN: 0.5pt 0cm;FONT-FAMILY: 宋体; FONT-SIZE: 15pt;'>在原审诉讼中，盈拓公司补充提交超级星饭团微信公众号娱乐信息截图作为证据。云智联公司补充提交以下证据：</div><div style='LINE-HEIGHT: 25pt; TEXT-INDENT: 30pt; MARGIN: 0.5pt 0cm;FONT-FAMILY: 宋体; FONT-SIZE: 15pt;'>1．云智联公司“超级星饭团”于2017年、2018年广告投放合同；</div><div style='LINE-HEIGHT: 25pt; TEXT-INDENT: 30pt; MARGIN: 0.5pt 0cm;FONT-FAMILY: 宋体; FONT-SIZE: 15pt;'>2．媒体微信公众号文章；</div><div style='LINE-HEIGHT: 25pt; TEXT-INDENT: 30pt; MARGIN: 0.5pt 0cm;FONT-FAMILY: 宋体; FONT-SIZE: 15pt;'>3．截图。</div><div style='LINE-HEIGHT: 25pt; TEXT-INDENT: 30pt; MARGIN: 0.5pt 0cm;FONT-FAMILY: 宋体; FONT-SIZE: 15pt;'>北京知识产权法院认为：云智联公司提交的证据能够证明云智联公司在诉争商标申请注册日前已经在娱乐信息等服务上使用了“超级星饭团”商标，已为相关公众所知晓并具有一定的影响力。诉争商标核定使用的“组织表演（演出）、娱乐服务、演出”等服务与云智联公司“超级星饭团”商标所使用的“娱乐信息”等服务关联性较大，属于类似服务。盈拓公司与云智联公司为同行业经营者，对云智联公司“超级星饭团”商标理应知晓，其在注册商标时亦应负有较高的注意义务。因此，诉争商标在“组织表演（演出）、娱乐服务、演出”等服务上的注册，已构成2013年商标法第三十二条关于“以不正当手段抢先注册他人已经使用并有一定影响的商标”之情形。</div><div style='LINE-HEIGHT: 25pt; TEXT-INDENT: 30pt; MARGIN: 0.5pt 0cm;FONT-FAMILY: 宋体; FONT-SIZE: 15pt;'>综上，北京知识产权法院依照《中华人民共和国行政诉讼法》第六十九条之规定，判决：驳回盈拓公司的诉讼请求。</div><div style='LINE-HEIGHT: 25pt; TEXT-INDENT: 30pt; MARGIN: 0.5pt 0cm;FONT-FAMILY: 宋体; FONT-SIZE: 15pt;'>盈拓公司不服原审判决，向本院提起上诉，请求撤销原审判决及被诉裁定，判令国家知识产权局重新作出裁定，其主要上诉理由为：一、云智联公司提交的证据2、4、5、6不足以证明在诉争商标申请日前，其对“超级星饭团”的使用属于商标性使用，亦不足以证明其对“超级星饭团”构成在先使用并具有一定影响。二、云智联公司提交的证据1与云智联公司并无关联性，不能证明在第41类服务上使用了“超级星饭团”商标，更无法证明其在微博中使用的“超级星饭团”具有知名度和影响力。因此，诉争商标的注册并未违反2013年商标法第三十二条的相关规定。</div><div style='LINE-HEIGHT: 25pt; TEXT-INDENT: 30pt; MARGIN: 0.5pt 0cm;FONT-FAMILY: 宋体; FONT-SIZE: 15pt;'>国家知识产权局、云智联公司服从原审判决。</div><div style='LINE-HEIGHT: 25pt; TEXT-INDENT: 30pt; MARGIN: 0.5pt 0cm;FONT-FAMILY: 宋体; FONT-SIZE: 15pt;'>经审理查明：原审法院查明的事实属实，且有诉争商标档案、被诉裁定、各方当事人在行政程序和诉讼程序中提交的证据及当事人陈述等在案佐证，本院予以确认。</div><div style='LINE-HEIGHT: 25pt; TEXT-INDENT: 30pt; MARGIN: 0.5pt 0cm;FONT-FAMILY: 宋体; FONT-SIZE: 15pt;'>另查，根据中央机构改革部署，原国家工商行政管理总局商标局、商标评审委员会的相关职责由国家知识产权局统一行使。</div><div style='LINE-HEIGHT: 25pt; TEXT-INDENT: 30pt; MARGIN: 0.5pt 0cm;FONT-FAMILY: 宋体; FONT-SIZE: 15pt;'>本院认为：</div><div style='LINE-HEIGHT: 25pt; TEXT-INDENT: 30pt; MARGIN: 0.5pt 0cm;FONT-FAMILY: 宋体; FONT-SIZE: 15pt;'>2013年商标法第三十二条规定，申请商标注册不得损害他人现有的在先权利，也不得以不正当手段抢先注册他人已经使用并有一定影响的商标。</div><div style='LINE-HEIGHT: 25pt; TEXT-INDENT: 30pt; MARGIN: 0.5pt 0cm;FONT-FAMILY: 宋体; FONT-SIZE: 15pt;'>“不得以不正当手段抢先注册他人在先使用并具有一定影响的商标”的规定，旨在规制抢注他人使用在先并有一定影响的商标的行为。认定诉争商标是否违反上述规定，应同时具备下列情形：1．未注册商标在诉争商标申请日之前已经使用并有一定影响；2．诉争商标与在先使用的未注册商标构成相同或近似商标；3．诉争商标指定使用的商品与在先使用的未注册商标所使用的商品构成相同或者类似商品；4．诉争商标申请人明知或者应知他人在先使用商标。</div><div style='LINE-HEIGHT: 25pt; TEXT-INDENT: 30pt; MARGIN: 0.5pt 0cm;FONT-FAMILY: 宋体; FONT-SIZE: 15pt;'>本案中，云智联公司提交的证据能够证明其在诉争商标申请注册之前已经在“娱乐信息”等服务上使用了“超级星饭团”商标。云智联公司提交的新浪微博发布的微博截屏，“超级星饭团”app在知名应用平台的后台、软件下载页面、评论页面截屏，AOS100移动推广数据平台关于“超级星饭团”app的版本记录、安卓端下载量等的截屏，云智联公司与影视演员、爱奇艺合作的微博等证据可以证明，云智联公司“超级星饭团”商标经过持续使用和宣传，已为相关公众所知晓并具有一定的影响。诉争商标与云智联公司在先使用的“超级星饭团”标志完全相同。同时，诉争商标核定使用的“组织表演（演出）、娱乐服务、演出”等服务与云智联公司“超级星饭团”商标所使用的“娱乐信息”等服务密切关联。另外，盈拓公司与云智联公司为同行业经营者，对云智联公司在先使用的“超级星饭团”商标理应知晓，但盈拓公司未尽合理避让义务，在类似服务上申请注册标志相同的商标，其行为难谓正当。因此，诉争商标在核定使用服务上的注册构成2013年商标法第三十二条规定的“不得以不正当手段抢先注册他人已经使用并有一定影响的商标”情形。原审判决及被诉裁定的对此认定并无不当，本院予以维持。盈拓公司的相关上诉理由缺乏事实和法律依据，本院不予支持。</div><div style='LINE-HEIGHT: 25pt; TEXT-INDENT: 30pt; MARGIN: 0.5pt 0cm;FONT-FAMILY: 宋体; FONT-SIZE: 15pt;'>综上所述，原审判决认定事实清楚，适用法律正确，程序合法，应予维持。盈拓公司的上诉理由不能成立，对其上诉请求，本院不予支持。依据《中华人民共和国行政诉讼法》第八十九条第一款第一项之规定，判决如下：</div><div id='6'  style='LINE-HEIGHT: 25pt; TEXT-INDENT: 30pt; MARGIN: 0.5pt 0cm;FONT-FAMILY: 宋体; FONT-SIZE: 15pt;'>驳回上诉，维持原判。</div><div id='2'  style='LINE-HEIGHT: 25pt; TEXT-INDENT: 30pt; MARGIN: 0.5pt 0cm;FONT-FAMILY: 宋体; FONT-SIZE: 15pt;'>一、二审案件受理费各一百元，均由北京盈拓文化传媒有限公司负担（均已交纳）。</div><div style='LINE-HEIGHT: 25pt; TEXT-INDENT: 30pt; MARGIN: 0.5pt 0cm;FONT-FAMILY: 宋体; FONT-SIZE: 15pt;'>本判决为终审判决。</div><div style='TEXT-ALIGN: right; LINE-HEIGHT: 25pt; MARGIN: 0.5pt 36pt 0.5pt 0cm;FONT-FAMILY: 宋体; FONT-SIZE: 15pt;'>审 判 长　孔庆兵</div><div style='TEXT-ALIGN: right; LINE-HEIGHT: 25pt; MARGIN: 0.5pt 36pt 0.5pt 0cm;FONT-FAMILY: 宋体; FONT-SIZE: 15pt;'>审 判 员　孙柱永</div><div style='TEXT-ALIGN: right; LINE-HEIGHT: 25pt; MARGIN: 0.5pt 36pt 0.5pt 0cm;FONT-FAMILY: 宋体; FONT-SIZE: 15pt;'>审 判 员　刘　岭</div><div style='TEXT-ALIGN: right; LINE-HEIGHT: 25pt; MARGIN: 0.5pt 36pt 0.5pt 0cm;FONT-FAMILY: 宋体; FONT-SIZE: 15pt;'>二〇二一年六月九日</div><div style='TEXT-ALIGN: right; LINE-HEIGHT: 25pt; MARGIN: 0.5pt 36pt 0.5pt 0cm;FONT-FAMILY: 宋体; FONT-SIZE: 15pt;'>法官助理　何　娟</div><div style='TEXT-ALIGN: right; LINE-HEIGHT: 25pt; MARGIN: 0.5pt 36pt 0.5pt 0cm;FONT-FAMILY: 宋体; FONT-SIZE: 15pt;'>书 记 员　郭媛媛</div></BODY></HTML>",
    "directory": [
        "1",
        "2",
        "2",
        "6",
        "2"
    ],
    "globalNet": "outer",
    "viewCount": "375"
    }
    # 只有第一次需要运行db_init()
    # db_init()
    add(res)





