import base64
import datetime
from distutils.command.build_scripts import first_line_re
import json
import random
import time
from base64 import b64decode, b64encode
from unicodedata import name

import execjs
import pyDes
import requests
from Crypto.Cipher import DES3
import os



class AESCipher:
    def __init__(self, key):
        self.key = key
        self.block_size = 8

    def pad(self, s):
        return s + (self.block_size - len(s) % self.block_size) * chr(self.block_size - len(s) % self.block_size)

    def unpad(self, s):
        return s[:-ord(s[len(s) - 1:])]

    def encrypt(self, raw, iv):
        raw = self.pad(raw)
        cipher = DES3.new(self.key, DES3.MODE_CBC, IV=iv)
        return b64encode(cipher.encrypt(raw.encode()))

    def decrypt(self, enc, iv):
        enc = b64decode(enc)
        cipher = DES3.new(self.key, DES3.MODE_CBC, iv=iv)
        return self.unpad(cipher.decrypt(enc)).decode('utf8')


def my_random(size):
    str1 = ""
    arr = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k',
           'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', 'A', 'B', 'C', 'D', 'E', 'F',
           'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']
    i = 0
    while i < size:
        str1 += arr[round(random.random() * (len(arr) - 1))]
        i += 1
    return str1


def strTobinary(data):
    result = []
    list1 = list(data)
    i = 0
    while i < len(list1):
        if i != 0:
            result.append(" ")
        item = list1[i]
        binaryStr = str(bin(ord(item))[2:])
        result.append(binaryStr)
        i += 1
    return "".join(result)


def cipher():
    date = datetime.datetime.now()
    timestamp = str(time.time()).replace('.', '')[:13]
    salt = my_random(24)
    year = str(date.year)
    month = date.month
    month = "0" + str(month) if month < 10 else str(month)
    day = "0" + str(date.day) if date.day < 10 else str(date.day)

    iv = year + month + day
    enc = AESCipher(salt)
    enc = enc.encrypt(timestamp, iv=iv.encode()).decode()
    str1 = salt + iv + enc
    ciphertext = strTobinary(str1)
    return ciphertext


def uuid():
    guid = ""
    i = 1
    while i <= 32:
        n = str(hex(int(random.random() * 16.0))).replace('0x', '')
        guid += n
        i += 1
    return guid


def send_request(url, headers, ws_params):
    sess = requests.session()
    req = sess.post(url=url, headers=headers, data=ws_params)
    assert req.status_code == 200
    return req.json()


def decrypt(data, secretkey):
    iv = time.strftime("%Y%m%d", time.localtime())
    des_obj = pyDes.triple_des(key=secretkey, IV=iv, padmode=pyDes.PAD_PKCS5, mode=pyDes.CBC)
    decodebs64data = base64.b64decode(data)
    s = des_obj.decrypt(decodebs64data).decode('utf-8')
    x = json.loads(s)
    return x


def getEncryptKey(password):
    file = "cpws_login.js"
    ctx = execjs.compile(open(file, encoding="utf-8").read())
    js = 'getpwd("{password}")'.format(password=password)
    encrypt_key = ctx.eval(js)
    return encrypt_key

def get_month(): #北京的是从10年开始，其他市的法院不确定
    #print(len(name))
    month=[]
    for i in range(2010,2022):
        for j in range(1,12):
            now=str(j) if j>=10 else "0"+str(j)
            next=str(j+1) if j+1>=10 else "0"+str(j+1)
            month.append("{}-{}-02 TO {}-{}-01".format(i,now,i,next))
        month.append("{}-{}-02 TO {}-01-01".format(i,12,i+1))
    i=2022
    for j in range(1,5):
        now=str(j) if j>=10 else "0"+str(j)
        next=str(j+1) if j+1>=10 else "0"+str(j+1)
        month.append("{}-{}-02 TO {}-{}-01".format(i,now,i,next))
    month.append("2010-01-01 TO 2010-01-01")
    return month
"""
def get_province_name(url,pageId,main_headers,verification_token):

    list_params = {
        'pageId': pageId,
        's2': '最高人民法院',
        'groupFields': 's45;s11;s4;s33;s42;s8;s6;s44',
        'queryCondition': '[{"key":"s8","value":"04"}]',
        'cfg': 'com.lawyee.judge.dc.parse.dto.SearchDataDsoDTO@leftDataItem',
        '__RequestVerificationToken': verification_token,
    }
    
    # 发送请求, 拿到返回结果
    data = send_request(url, main_headers, list_params)
    p_name=[]
    for d in data['result']['s33']:
        p_name.append(d['value'])
    return p_name
"""
    
def get_name(url, main_headers,verification_token):
    list_params = {
                    'provinceCode':'0',
                    'searchParent':'true',
                    'cfg': 'com.lawyee.judge.dc.parse.dto.LoadDicDsoDTO@loadFy',
                    '__RequestVerificationToken': verification_token,
                }
    name=[]#所有法院一个list
    name2=[] #每个城市的法院组成一个小list

    first_data=send_request(url, main_headers, list_params) #所有省的最高法院
    for province in first_data['result']['fy']:
        print(province)
        name.append(province['name'])
        name2.append([])
        name2[-1].append(province['name'])
        if province['id']=='0':
            continue
        list_params['provinceCode']=province['id']
        province_data= send_request(url, main_headers, list_params) #本省的中高级法院
        for fy in province_data['result']['fy']:
            if fy['id']==province['id']:
                continue
            name.append(fy['name'])
            name2[-1].append(fy['name'])
            list_params['provinceCode']=fy['id']   
            fy_data=send_request(url, main_headers, list_params) #中高级法院下属的基层法院
            for n_fy in fy_data['result']['fy']:
                if n_fy['id']==fy['id']:
                    continue
                name.append(n_fy['name'])
                name2[-1].append(n_fy['name'])    
    #print(name)
    #print(name2)
    #province_data= send_request(url, main_headers, list_params)
    #print(province_data)
    # print(province_data['result']['fy'])
    #assert province_data["code"] == 1
    
    return name,name2


if __name__ == '__main__':
    # 通过登录拿到Cookie, 放到headers里
    # wenshu = wenshu()
    # # 获取登陆后的Cookie
    # cookies = wenshu.send_login()
    # # 将cookie转换为字符串
    # json_cookie = ''
    # for cookie in cookies:
    #     name = cookie['name']
    #     value = cookie['value']
    #     json_cookie += name + '=' + value + '; '
    # # 退出selenium浏览器自动化
    # # wenshu.chrome.quit()
    # print(json_cookie)

    # 账号, 密码
    # username = "18810721592"
    # password = "Abc#123456"
    # cpws_heardes = {
    #     "Accept": "*/*",
    #     "Accept-Encoding": "gzip, deflate, br",
    #     "Accept-Language": "en",
    #     "Connection": "keep-alive",
    #     "Content-Length": "440",
    #     "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    #     "Host": "account.court.gov.cn",
    #     "Origin": "https://account.court.gov.cn",
    #     "Pragma": "no-cache",
    #     "Referer": "https://account.court.gov.cn/app?back_url=https%3A%2F%2Faccount.court.gov.cn%2Foauth%2Fauthorize%3Fresponse_type%3Dcode%26client_id%3Dzgcpwsw%26redirect_uri%3Dhttps%253A%252F%252Fwenshu.court.gov.cn%252FCallBackController%252FauthorizeCallBack%26state%3Df22de1f8-408a-486c-bef1-0535fd5d7cb7%26timestamp%3D1633526741958%26signature%3D5A8EE0767D10C2D7AF05B5389678D74A3B2478245776F5E8BCC119E401FC9633%26scope%3Duserinfo",
    #     'User-Agent': 'Mozilla/5.0 (iPhone; CPU OS 10_15_5 (Ergänzendes Update) like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/12.1.1 Mobile/14E304 Safari/605.1.15',
    #     "X-Requested-With": "XMLHttpRequest"
    # }
    main_headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 6_0 like Mac OS X) AppleWebKit/536.26 (KHTML, like Gecko) Version/6.0 Mobile/10A5376e Safari/8536.25',
        # 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.67 Safari/537.36',
        # 'Host': 'wenshuapp.court.gov.cn',
        # 'Origin': 'https://wenshuapp.court.gov.cn',
        # 'sec-ch-ua': 'Google Chrome";v="89", "Chromium";v="89", ";Not A Brand";v="99',
        # 'Referer': f'Referer: https://wenshuapp.court.gov.cn/website/wenshu/181217BMTKHNT2W0/index.html?pageId={pageId}',
        # 'Accept': '*/*',
        # 'Accept-Encoding': 'gzip, deflate, br',
        # 'Accept-Language': 'zh-CN,zh;q=0.9',
        # 'Connection': 'keep-alive',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Cookie': 'SESSION=e26430be-72f4-4add-a460-28726914a719',
        # '; wzws_cid=f4e3042d4574e0f94aa94c62f3afddbb958792ec770a7372b43149fc4bc2896818ee2b95d2c3bb17884c3f89127ec1ecca53041a401d15acb11f8b1008f097182e735de9c95d379ccc1187e1b5f1ae10'
    }

    # 返回操作成功即登录成功
    # session = requests.Session()
    # login_url = "https://account.court.gov.cn/api/login"
    # data = {
    #     "username": username,
    #     "password": getEncryptKey(password),
    #     "appDomain": "wenshu.court.gov.cn"
    # }
    # response = session.post(url=login_url, data=data, headers=cpws_heardes)
    # print(response.text)
    # print(session.cookies.get_dict())
    # main_url = "https://wenshuapp.court.gov.cn/website/wenshu/181029CR4M5A62CH/index.html?#"
    # main_response = session.get(url=main_url, headers=main_headers)
    # print(main_response.text)

    # 构造POST请求参数, 编写逻辑来自逆向JS
    # 模拟生成pageId, ciphertext, __RequestVerificationToken
    url = "https://wenshuapp.court.gov.cn/website/parse/rest.q4w"
    pageId = uuid()
    ciphertext = cipher()
    verification_token = my_random(24)
    ######## zhai code
    
    month=get_month()

##获取或读取法院名
    name_path=os.path.dirname(__file__)+"/fy_name.txt"

    if os.path.exists(name_path):
        with open(name_path,"r",encoding='UTF-8') as f:
            name,name2=json.load(f)
    else:
        name,name2=get_name(url, main_headers,verification_token)
        with open(name_path,"w",encoding='UTF-8') as f:
            j_n=json.dumps([name,name2],ensure_ascii=False)
            f.write(j_n)

    print(name[0])
    print(name2[0])
    #p_name=get_province_name(url,pageId, main_headers,verification_token)
    #print(p_name)
    #print(len(month))
    #print(len(name))
######## zhai code
    for x in name:
        for y in month:
            query_list=[{"key":"s8","value":"04"},{"key":"cprq","value":y},{"key":"s2","value":x}]
            for num in range(1,21):
                # 列表爬虫
                list_params = {
                    'pageId': pageId,
                    's8': '04',
                    'sortFields': 's50:desc',
                    'ciphertext': ciphertext,
                    'pageNum': num,
                    'pageSize': 50,
                    'queryCondition': str(query_list),
                    'cfg': 'com.lawyee.judge.dc.parse.dto.SearchDataDsoDTO@queryDoc',
                    '__RequestVerificationToken': verification_token,
                }
                
                # 发送请求, 拿到返回结果
                data = send_request(url, main_headers, list_params)
                #print(data)
                assert data["code"] == 1
                # 解密返回结果
                res = decrypt(data["result"], data["secretKey"])

                #print(json.dumps(res, indent=4, ensure_ascii=False))
                print(x,y)
                print(len(list(res["relWenshu"].keys())))
                if len(list(res["relWenshu"].keys()))==0:
                    break
                # 正文爬虫
                # docId = random.choice(list(res["relWenshu"].keys()))
                
                for docId in list(res["relWenshu"].keys()):
                    print(docId)
                    doc_params = {
                        'docId': docId,
                        'ciphertext': ciphertext,
                        'cfg': 'com.lawyee.judge.dc.parse.dto.SearchDataDsoDTO@docInfoSearch',
                        '__RequestVerificationToken': verification_token,
                    }
                    # 发送请求, 拿到返回结果
                    data = send_request(url, main_headers, doc_params)
                    #print(data)
                    assert data["code"] == 1
                    # 解密返回结果
                    res = decrypt(data["result"], data["secretKey"])
                    print(json.dumps(res, indent=4, ensure_ascii=False))
                break
            #break
        break