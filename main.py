import json
import math
import random
import time
import requests

from typing import Dict, Any
import os, os.path as op
from selenium import webdriver
from tqdm import trange, tqdm
from config import ua_list, username, password, driver_path, headers_path
from utils import DES3_Cracker, uuid, cipher, rand_str


# 裁判文书网自动化爬虫, 支持多进程爬取
class WenShuCrawler:
    def __init__(self):
        # Common headers, Cookies (支持缓存)
        if op.exists(headers_path):
            self.headers = json.load(open(headers_path))
            self.user_agent = self.headers["User-Agent"]
        else:
            self.user_agent = random.choice(ua_list)
            self.headers = {
                'User-Agent': self.user_agent,
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'Cookie': '',
            }

        # Driver Part: driver options
        self.options = webdriver.ChromeOptions()
        self.options.add_argument(f"User-Agent={self.user_agent}")  # 确保前后请求的UA一致, 否则session无效
        self.options.add_argument('disable-infobars')  # 让浏览器不显示自动化测试
        self.driver = None
        # Driver Part: url, element xpath
        self.login_url = 'https://wenshuapp.court.gov.cn/website/wenshu/181010CARHS5BS3C/index.html?open=login'
        self.user_input_xpath = '//*[@id="root"]/div/form/div/div[1]/div/div/div/input'
        self.pass_input_xpath = '//*[@id="root"]/div/form/div/div[2]/div/div/div/input'
        self.submit_btn_xpath = '//*[@id="root"]/div/form/div/div[3]/span'

        # Crawler Part: url, session
        self.api_url = "https://wenshuapp.court.gov.cn/website/parse/rest.q4w"
        self.session = requests.Session()
        # Crawler Part: common post params
        self.pageId = uuid()
        self.ciphertext = cipher()
        self.verification_token = rand_str()
        self.cracker = DES3_Cracker()
        # Crawler Part: query config
        self.base_query = {"key": "s8", "value": "04"}  # 行政诉讼案件
        # Crawler Part: general config
        self.mproc = False
        self.crawl_unit = 150  # max_limit<=1

        # Initialize Crawler
        if not op.exists(headers_path):
            self.update_cookie()

    # 用driver模拟登录, 实现Cookie更新
    def update_cookie(self):
        self.driver = webdriver.Chrome(driver_path, options=self.options)
        # 打开登录页面
        self.driver.get(self.login_url)
        self.driver.implicitly_wait(10)
        self.driver.maximize_window()  # 最大化浏览器
        # 切换到iframe登录框, 输入用户名和密码后提交
        self.driver.switch_to.frame('contentIframe')
        self.driver.find_element_by_xpath(self.user_input_xpath).send_keys(username)
        self.driver.find_element_by_xpath(self.pass_input_xpath).send_keys(password)
        self.driver.find_element_by_xpath(self.submit_btn_xpath).click()
        time.sleep(3)
        # 更新cookie并写入缓存
        cookies = self.driver.get_cookies()
        cookie_text = ''.join([f"{cookie['name']}={cookie['value']}; " for cookie in cookies])
        assert "SESSION=" in cookie_text
        self.headers["Cookie"] = cookie_text
        json.dump(self.headers, open(headers_path, "w+"), ensure_ascii=False, indent=4)
        print(f"Updated Cookie: {cookie_text}")
        # 退出selenium浏览器自动化
        self.driver.quit()

    # set random delay to avoid high-parallelism collisions
    def random_delay(self, max_delay: int = 2):
        time.sleep(random.uniform(0, max_delay))

    # 发出POST请求并检查状态码, 若失败则更新Cookie直至请求成功
    def post(self, params: Dict[str, Any]):
        data = {"code": -1}
        while data["code"] != 1:
            if data["code"] != -1:
                self.update_cookie()
            req = self.session.post(self.api_url, data=params, headers=self.headers)  # "headers="不能省略
            assert req.status_code == 200
            data = req.json()
        return data

    # crawl a fixed number of docIds
    def once_list_crawler(self, query_text: str, turn_id: int):
        params = {
            'pageId': self.pageId,
            self.base_query["key"]: self.base_query["value"],  # 's8': '04'
            'sortFields': 's50:desc',
            'ciphertext': self.ciphertext,
            'pageNum': turn_id,
            'pageSize': self.crawl_unit,
            'queryCondition': query_text,  # '[{"key":"s8","value":"04"},{"key":"s2","value":"北京市高级人民法院"}]',
            'cfg': 'com.lawyee.judge.dc.parse.dto.SearchDataDsoDTO@queryDoc',
            '__RequestVerificationToken': self.verification_token,
        }
        # 发送请求, 拿到返回结果并解密
        data = self.post(params)
        return self.cracker.decrypt(data["secretKey"], data["result"])

    # invoke once_list_crawler multiple times to get all query result docIds of a condition set
    def multi_turn_list_crawler(self, add_query: Dict[str, str], pid: int = 0, queue=None):
        start_t, results = time.perf_counter(), []
        query_text = str([self.base_query] + [{"key": k, "value": v} for k, v in add_query.items()])
        turn_results = self.once_list_crawler(query_text, turn_id=1)
        count = turn_results["queryResult"]["resultCount"]
        assert count <= 1000
        for turn_id in trange(1, math.ceil(count / self.crawl_unit) + 1):
            if turn_id > 1:
                turn_results = self.once_list_crawler(query_text, turn_id)
            doc_indices = list(turn_results["relWenshu"].keys())
            assert len(doc_indices) > 0
            results += doc_indices
        assert len(set(results)) == count
        if queue is not None:
            queue.put(results)
        print("\nEND Proc {}, cond {}, {} results, in {:.1f}s\n".format(pid, add_query, len(results), time.perf_counter() - start_t))
        return results

    # crawl detailed article via docId
    def detail_crawler(self, doc_id: str):
        params = {
            'docId': doc_id,
            'ciphertext': self.ciphertext,
            'cfg': 'com.lawyee.judge.dc.parse.dto.SearchDataDsoDTO@docInfoSearch',
            '__RequestVerificationToken': self.verification_token,
        }
        # 发送请求, 拿到返回结果并解密
        data = self.post(params)
        return self.cracker.decrypt(data["secretKey"], data["result"])

    # main function
    def run_crawler(self):
        # 法院列表爬虫
        # 文书列表爬虫
        docId_list = self.multi_turn_list_crawler(add_query={"s2": "北京市高级人民法院", "cprq": "2021-05-01 TO 2021-06-01"})
        # 文书正文爬虫
        for docId in tqdm(docId_list):  # "a8f0be8fe8914c29a7d2ad53000b03f6"
            res = self.detail_crawler(docId)
            # print(json.dumps(res, ensure_ascii=False, indent=4))


if __name__ == '__main__':
    crawler = WenShuCrawler()
    crawler.run_crawler()
