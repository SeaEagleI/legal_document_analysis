# -*- coding: utf-8 -*-
import sqlite3
import ujson

# from bs4 import BeautifulSoup

'''
数据库：
- document 基本包含全部信息，list和dict会被展平成字符串
  不包含：（重复）
  wenshuAy
  rowkey
  特殊：
  id即为s5，主键类型是text，但其他表的主键都是自增的integer
  
- party(s17) 单独包含party信息，出现一次增加一条，不另设关系表，下同
  ('id', 'name', 'doc_id')
- law(s47)  full字段 = name +clause
  ('id', 'full', 'name', 'clause', 'doc_id')
- keyword(s45)
  ('id', 'word', 'doc_id')
'''


def db_init(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
    create table document
    (
        id   text
            constraint document_pk
                primary key,
        s1       text,
        s2       text,
        s3       text,
        s4       text,
        s6       text,
        s7       text,
        s8       text,
        s9       text,
        s10      text,
        s11      text,
        s17      text,
        s22      text,
        s23      text,
        s25      text,
        s26      text,
        s27      text,
        s28      text,
        s31      text,
        s32      text,
        s33      text,
        s40      text,
        s41      text,
        s42      text,
        s43      text,
        s44      text,
        s45      text,
        s47      text,
        viewCount text,
        qwContent text,
        relWenshu text,
        directory text,
        globalNet text
    );
    ''')
    cursor.execute('''
    create table party
    (
        id integer
            constraint party_pk
                primary key autoincrement,
        name text,
        doc_id text
    );
    ''')
    # cursor.execute('''
    # create unique index party_name_uindex
    # on party (name);
    # ''')
    # cursor.execute('''
    # create table party_document_rel
    # (
    #     id integer
    #         constraint party_document_rel_pk
    #             primary key autoincrement,
    #     party_id integer,
    #     doc_id text
    # );
    # ''')
    cursor.execute('''
    create table law
    (
        id integer
            constraint law_pk
                primary key autoincrement,
        full text,
        name text,
        clause text,
        doc_id text
    );
    ''')
    # cursor.execute('''
    # create unique index law_full__uindex
    # on law (full);
    # ''')
    # cursor.execute('''
    # create table "law_document_rel"
    # (
    #     id integer
    #         constraint "law_document-rel_pk"
    #             primary key autoincrement,
    #     law_id integer,
    #     doc_id text
    # );
    # ''')
    cursor.execute('''
    create table keyword
    (
        id integer
            constraint party_pk
                primary key autoincrement,
        word text,
        doc_id text
    );
    ''')
    # cursor.execute('''
    # create unique index keyword_word_uindex
    # on keyword (word);
    # ''')
    # cursor.execute('''
    # create table keyword_document_rel
    # (
    #     id integer
    #         constraint party_document_rel_pk
    #             primary key autoincrement,
    #     keyword_id integer,
    #     doc_id text
    # );
    # ''')
    conn.commit()
    cursor.close()
    conn.close()


# 插入document表
def add_doc(res, cursor):
    # 允许存入document表的key
    allow_keys = ['id', 's1', 's2', 's3', 's4', 's6', 's7', 's8', 's9', 's10', 's11', 's17', 's22', 's23', 's25', 's26',
                  's27', 's28', 's31', 's32', 's33', 's40', 's41', 's42', 's43', 's44', 's45', 's47', 'qwContent', 'viewCount', 'relWenshu', 'directory', 'globalNet']
    # 需要展平的字段
    flatten_keys = ['s11', 's17', 's45', 'directory']
    json_keys = ['relWenshu']
    # 补全
    for key in allow_keys:
        if key not in res:
            res[key] = ''
    # 拼接sql
    field_str = ""
    parma_str = ""
    mapping_list = []
    for key in allow_keys:
        # res中已经替换s5为id了，s5无需替换
        field_str += key + ', '
        parma_str += '?, '
    for key in allow_keys:
        value = res[key]
        # list展平
        if (key in flatten_keys) and isinstance(value, list):
            temp = ''
            for item in value:
                temp += item + ';'
            value = temp[0:-1]
        # 转json
        if (key in json_keys) and isinstance(value, list):
            value = ujson.dumps(value)
        # s47展平
        if key == 's47':
            temp = ''
            for item in value:
                # 出现过报错KeyError: 'fgmc'; 不知道是不是有其他key或者s47中可以有空dict
                if "fgmc" not in item:
                    item["fgmc"] = ""
                if "tkx" not in item:
                    item["tkx"] = ""
                temp += item["fgmc"] + item["tkx"] + ";"
            value = temp[0:-1]
        mapping_list.append(value)
    field_str = field_str[0:-2]
    parma_str = parma_str[0:-2]
    doc_sql = 'insert into document (' + field_str + ') values (' + parma_str + ')'
    # print(doc_sql)
    cursor.execute(doc_sql, tuple(mapping_list))
    # print('插入' + str(cursor.rowcount) + '条数据')


# 插入party当事人表
def add_party(res, cursor):
    party_sql = "insert into party (name, doc_id) values (?, ?)"
    # rel_sql = "insert into party_document_rel (party_id, doc_id) values (?, ?)"
    for name in res['s17']:
        # print(party_sql, name)
        cursor.execute(party_sql, (name, res['id']))
        # party_id = cursor.lastrowid
        # cursor.execute(rel_sql, (party_id, res['id']))


# 插入law法律条款表
def add_law(res, cursor):
    law_sql = "insert into law (full, name, clause, doc_id) values (?, ?, ?, ?)"
    # rel_sql = "insert into law_document_rel (law_id, doc_id) values (?, ?)"
    for d in res['s47']:
        if "fgmc" not in d:
            d["fgmc"] = ""
        if "tkx" not in d:
            d["tkx"] = ""
        cursor.execute(law_sql, (d['fgmc'] + d['tkx'], d['fgmc'], d['tkx'], res['id']))
        # law_id = cursor.lastrowid
        # cursor.execute(rel_sql, (law_id, res['id']))

# 插入keyword关键词表
def add_keyword(res, cursor):
    keyword_sql = "insert into keyword (word, doc_id) values (?, ?)"
    # rel_sql = "insert into keyword_document_rel (keyword_id, doc_id) values (?, ?)"
    for word in res['s45']:
        # print(party_sql, name)
        cursor.execute(keyword_sql, (word, res['id']))
        # keyword_id = cursor.lastrowid
        # cursor.execute(rel_sql, (keyword_id, res['id']))

# 每次添加1k个输出一次
def add(resList, db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    count = 0
    total = len(resList)
    for res in resList:
        add_doc(res, cursor)
        add_party(res, cursor)
        add_law(res, cursor)
        add_keyword(res, cursor)
        count += 1
        if count % 1000 == 0:
            print(f'已插入{count/1000}k条数据，共{total}条，当前完成了{count/total*100:.2f}%')
    conn.commit()
    cursor.close()
    conn.close()


if __name__ == '__main__':
    db_path = '../data/judge.db'
    # 只有第一次需要运行db_init()
    db_init(db_path)
    with open("../data/processed/processed.json", "r") as f:
        resList = ujson.load(f)
        add(resList, db_path)
