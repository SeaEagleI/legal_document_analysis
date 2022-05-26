import json
import random
import time
import requests
from Crypto.Cipher import DES3
from base64 import b64decode, b64encode
from selenium import webdriver


class AESCipher:
    def __init__(self):
        self.block_size = 8
        self.iv = time.strftime("%Y%m%d", time.localtime()).encode()

    def pad(self, s):
        return s + (self.block_size - len(s) % self.block_size) * chr(self.block_size - len(s) % self.block_size)

    def unpad(self, s):
        return s[:-ord(s[len(s) - 1:])]

    def encrypt(self, key, raw):
        raw = self.pad(raw)
        cipher = DES3.new(key, DES3.MODE_CBC, IV=self.iv)
        return b64encode(cipher.encrypt(raw.encode()))

    def decrypt(self, key, enc):
        enc = b64decode(enc)
        cipher = DES3.new(key, DES3.MODE_CBC, IV=self.iv)
        return json.loads(self.unpad(cipher.decrypt(enc)).decode('utf-8'))


def randstr(size):
    arr = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k',
           'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', 'A', 'B', 'C', 'D', 'E', 'F',
           'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']
    return "".join([random.choice(arr) for _ in range(size)])


def str2bin(raw):
    return " ".join([str(bin(ord(c))[2:]) for c in raw])


def cipher():
    timestamp = str(time.time()).replace('.', '')[:13]
    salt = randstr(24)
    iv = time.strftime("%Y%m%d", time.localtime())
    enc = AESCipher().encrypt(salt, timestamp).decode()
    str1 = salt + iv + enc
    return str2bin(str1)


def uuid():
    arr = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'a', 'b', 'c', 'd', 'e', 'f']
    return "".join([random.choice(arr) for _ in range(32)])


def _post(sess, url, params, headers):
    req = sess.post(url=url, data=params, headers=headers)
    assert req.status_code == 200
    return req.json()


class WenShu:
    def __init__(self, ua):
        # 账号, 密码
        self.user = "18810721592"
        self.passwd = "Abc#123456"
        # Driver params
        self.driver_path = 'driver/chromedriver.exe'
        # 1）修改UA, 确保与之后请求的UA一致（只有UA一致session才有效）; 2）让浏览器不显示自动化测试
        options = webdriver.ChromeOptions()
        options.add_argument(f"User-Agent={ua}")
        options.add_argument('disable-infobars')
        self.driver = webdriver.Chrome(executable_path=self.driver_path, options=options)
        # Url & Element params
        self.login_url = 'https://wenshuapp.court.gov.cn/website/wenshu/181010CARHS5BS3C/index.html?open=login'
        self.user_input_xpath = '//*[@id="root"]/div/form/div/div[1]/div/div/div/input'
        self.pass_input_xpath = '//*[@id="root"]/div/form/div/div[2]/div/div/div/input'
        self.submit_btn_xpath = '//*[@id="root"]/div/form/div/div[3]/span'
        # Cookies
        self.cookie_text = ""

    def auto_login(self):
        # 模拟登录，获得Cookie
        self.driver.get(self.login_url)
        self.driver.implicitly_wait(10)
        # 最大化浏览器
        self.driver.maximize_window()
        # 因为登录框在iframe框中，需要先切换到iframe中
        self.driver.switch_to.frame('contentIframe')
        self.driver.find_element_by_xpath(self.user_input_xpath).send_keys(self.user)
        self.driver.find_element_by_xpath(self.pass_input_xpath).send_keys(self.passwd)
        # time.sleep(1)
        self.driver.find_element_by_xpath(self.submit_btn_xpath).click()
        time.sleep(5)
        # 拿到cookie, 并转换为字符串
        cookies = self.driver.get_cookies()
        self.cookie_text = ''.join([f"{cookie['name']}={cookie['value']}; " for cookie in cookies])
        assert "SESSION=" in self.cookie_text
        # 退出selenium浏览器自动化
        self.driver.quit()
        return self.cookie_text


if __name__ == '__main__':
    # 公共请求头
    headers = {
        # 'User-Agent': 'Mozilla/5.0 (iPhone; CPU OS 10_15_5 (Ergänzendes Update) like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/12.1.1 Mobile/14E304 Safari/605.1.15',
        'User-Agent': 'Mozilla/5.0 (Linux; Android 11; SAMSUNG-SM-T377A Build/NMF26X) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Mobile Safari/537.36',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        # 'Cookie': 'SESSION=2c32f77e-b4d4-4719-aeb0-398c90c9d32a',
    }

    # 获取登陆后的Cookie
    cookie_text = WenShu(headers["User-Agent"]).auto_login()
    print(cookie_text)

    # 构造POST请求参数, 编写逻辑来自对JS的逆向工程
    # 模拟生成pageId, ciphertext, __RequestVerificationToken
    api_url = "https://wenshuapp.court.gov.cn/website/parse/rest.q4w"
    pageId = uuid()
    ciphertext = cipher()
    verification_token = randstr(24)
    # headers["Cookie"] = "SESSION=2ded3315-28ef-48fd-9697-cf97053c9902; "
    headers['Cookie'] = cookie_text
    session = requests.Session()

    # 列表爬虫
    list_params = {
        'pageId': pageId,
        's8': '04',
        'sortFields': 's50:desc',
        'ciphertext': ciphertext,
        'pageNum': 1,
        'pageSize': 5,
        'queryCondition': '[{"key":"s8","value":"04"},{"key":"s33","value":"北京市"}]',
        'cfg': 'com.lawyee.judge.dc.parse.dto.SearchDataDsoDTO@queryDoc',
        '__RequestVerificationToken': verification_token,
    }
    # 发送请求, 拿到返回结果
    data = _post(session, api_url, list_params, headers)
    assert data["code"] == 1
    # 解密返回结果
    res = AESCipher().decrypt(data["secretKey"], data["result"])
    print(json.dumps(res, indent=4, ensure_ascii=False))

    # 正文爬虫
    # docId = random.choice(list(res["relWenshu"].keys()))
    docId = "a8f0be8fe8914c29a7d2ad53000b03f6"
    print(docId)
    doc_params = {
        'docId': docId,
        'ciphertext': ciphertext,
        'cfg': 'com.lawyee.judge.dc.parse.dto.SearchDataDsoDTO@docInfoSearch',
        '__RequestVerificationToken': verification_token,
    }
    # 发送请求, 拿到返回结果
    data = _post(session, api_url, doc_params, headers)
    assert data["code"] == 1
    # 解密返回结果
    res = AESCipher().decrypt(data["secretKey"], data["result"])
    print(json.dumps(res, indent=4, ensure_ascii=False))
