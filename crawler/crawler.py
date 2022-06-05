import re
import math
import random
import time
import requests
import multiprocessing

import numpy as np
import os, os.path as op
from typing import Dict, Any, List
from datetime import timedelta, datetime as dt
from selenium import webdriver
from tqdm import trange, tqdm
from config import Config
from utils import Cracker, load_data, dump_data


# 裁判文书网自动化爬虫, 支持多进程爬取 (2022-06-01)
class WenShuCrawler:
    def __init__(self, config: Config):
        # Config file
        self.args = config
        # Common headers, Cookies (支持缓存)
        if op.exists(self.args.headers_path):
            self.headers = load_data(self.args.headers_path)
            self.user_agent = self.headers["User-Agent"]
        else:
            self.user_agent = random.choice(self.args.ua_list)
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
        self.cracker = Cracker()
        self.pageId = self.cracker.uuid()
        self.ciphertext = self.cracker.cipher()
        self.verification_token = self.cracker.rand_str()
        # Crawler Part: query config
        self.base_query = {"key": "s8", "value": "04"}  # 行政诉讼案件
        self.desc2key = {  # 候选分流字段, 用于进行值统计
            "case_type": "s8",  # 基本条件 （key0）
            "court_name": "s2",  # LV1字段 （key1）
            "year": "s42",  # LV2辅助字段: 轻微不全, 无重复, 分布较均衡
            "date": "cprq",  # LV2字段: 不支持值统计 （key2）
            "doc_type": "s6",  # LV3字段: 全, 无重复, 分布严重不均 （key3）
            "case_no": "s7",  # LV4字段: 返回结果数上限为35 （key4）
            # "keyword": "s45",  # 未使用: 严重不全, 重复较多
            # "province": "s33",  # 未使用
            # "court_level": "s4",  # 未使用
        }
        self.key0 = "s8"  # case_type
        self.key1 = "s2"  # court_name
        self.key2 = "cprq"  # date
        self.key3 = "s6"  # doc_type
        self.key4 = "s7"  # case_no
        self.date_tplt = "%Y-%m-%d"
        # Crawler Part: general config
        # self.crawl_unit = 25  # 极限大小, 速度最快; unit需要是1000的因子, 否则遇到长度为1k的query在请求最后一页时会得到空结果
        self.use_cache = self.args.use_cache
        self.crawl_units = [150, 125, 100, 50, 25, 10]  # 动态unit机制: 优先使用最大unit(最快), 出现错误再逐步下调unit
        self.crawl_limit = 1000  # 每种条件组合的返回结果上限
        self.max_retry = 5
        # Multi-Proc Part: 默认在四个主要时间瓶颈任务上使用多进程并行实现
        self.num_workers = self.args.num_workers
        self.num_queries = -1
        self.num_docs = -1
        self.proc_unit = -1
        self.do_split = self.args.do_split  # 结果太大, 默认分块保存, 最后再合并

        # Initialize Crawler
        if not op.exists(self.args.headers_path):
            self.update_cookie()
        if op.exists(self.args.lock_path):
            os.remove(self.args.lock_path)
        # Result data: 不在成员变量中存储结果数据, 节约并行开销
        # Preprocess
        self.repl_dict = {
            "<.*?>": "\n",
            " +": "",
            "\n+": "\n",
            "^\n|\n$": "",
        }

    # 用driver模拟登录, 实现Cookie更新
    def update_cookie(self):
        self.driver = webdriver.Chrome(self.args.driver_path, options=self.options)
        # 打开登录页面
        self.driver.get(self.login_url)
        self.driver.implicitly_wait(10)
        self.driver.maximize_window()  # 最大化浏览器
        # 切换到iframe登录框, 输入用户名和密码后提交
        self.driver.switch_to.frame('contentIframe')
        self.driver.find_element_by_xpath(self.user_input_xpath).send_keys(self.args.username)
        self.driver.find_element_by_xpath(self.pass_input_xpath).send_keys(self.args.password)
        self.driver.find_element_by_xpath(self.submit_btn_xpath).click()
        time.sleep(3)
        # 更新cookie并写入缓存
        cookies = self.driver.get_cookies()
        cookie_text = ''.join([f"{cookie['name']}={cookie['value']}; " for cookie in cookies])
        assert "SESSION=" in cookie_text
        self.headers["Cookie"] = cookie_text
        dump_data(self.headers, self.args.headers_path)
        print(f"Updated Cookie: {cookie_text}")
        # 退出selenium浏览器自动化
        self.driver.quit()

    # 发出POST请求并检查状态码, 若失败则更新Cookie直至请求成功
    def post(self, params: Dict[str, Any]):
        data: Dict[str, Any] = {"code": -1}
        while data["code"] != 1:
            if data["code"] != -1:
                # 引入互斥锁文件, 为update_cookie函数上锁
                loop_cnt = 0
                while op.exists(self.args.lock_path):  # 段1
                    loop_cnt += 1
                    time.sleep(1)
                if loop_cnt:  # 段2
                    data["code"] = -1
                    self.headers = load_data(self.args.headers_path)  # 成员变量在多进程中不会同步, 需要手动更新
                    continue
                open(self.args.lock_path, "w+").write("")  # 段3: 假设段2和段3执行足够快, 则不会有两个进程同时越过段1（实验表明假设满足90%的情况）
                self.update_cookie()
                os.remove(self.args.lock_path)
            req = self.session.post(self.api_url, data=params, headers=self.headers)  # "headers="不能省略
            assert req.status_code == 200
            data = req.json()
        return data

    # convert date to str
    def date2str(self, date: dt):
        return dt.strftime(date, self.date_tplt)

    # 法院列表爬虫
    def court_list_crawler(self):
        if self.use_cache and op.exists(self.args.court_path):
            return load_data(self.args.court_path)
        params = {
            'provinceCode': '',  # 上级法院编号
            'searchParent': 'true',
            'cfg': 'com.lawyee.judge.dc.parse.dto.LoadDicDsoDTO@loadFy',
            '__RequestVerificationToken': self.verification_token,
        }
        court_list, supreme_court_id = [], '0'
        # 第1层数据: 最高法院 -> 全国各省级行政单位的高级法院 (带"高级")
        params['provinceCode'] = supreme_court_id
        high_court_list = self.post(params)['result']['fy']
        for high_court in tqdm(high_court_list, desc="Crawling Courts"):
            court_list.append(high_court)
            if high_court['id'] == supreme_court_id:
                continue
            # 第2层数据: 本省的高级法院 -> 本省下各市的中级法院 (带"中级")
            params['provinceCode'] = high_court['id']
            inter_court_list = self.post(params)['result']['fy']
            for inter_court in inter_court_list:
                if inter_court['id'] == high_court['id']:
                    continue
                court_list.append(inter_court)
                # 第3层数据: 本市的中级法院 -> 本市辖区内各县级市、县、区的基层法院 (不带"级")
                params['provinceCode'] = inter_court['id']
                primary_court_list = self.post(params)['result']['fy']
                for primary_court in primary_court_list:
                    if primary_court['id'] == inter_court['id']:
                        continue
                    court_list.append(primary_court)
        dump_data(court_list, self.args.court_path)
        return court_list

    # crawl a fixed number of docIds
    def once_doc_list_crawler(self, query_text: str, crawl_unit: int = 5, turn_id: int = 1):
        params = {
            'pageId': self.pageId,
            self.base_query["key"]: self.base_query["value"],  # 's8': '04'
            'sortFields': 's50:desc',
            'ciphertext': self.ciphertext,
            'pageNum': turn_id,
            'pageSize': crawl_unit,  # 5 for count_only
            'queryCondition': query_text,  # '[{"key":"s8","value":"04"},{"key":"s2","value":"北京市高级人民法院"}]',
            'cfg': 'com.lawyee.judge.dc.parse.dto.SearchDataDsoDTO@queryDoc',
            '__RequestVerificationToken': self.verification_token,
        }
        # 发送请求, 拿到返回结果并解密
        data = self.post(params)
        return self.cracker.decrypt(data["secretKey"], data["result"])

    # invoke once_list_crawler multiple times to get all query result docIds of a condition set
    def doc_list_crawler(self, add_query: Dict[str, str], crawl_unit):
        results = []
        query_text = str([self.base_query] + [{"key": k, "value": v} for k, v in add_query.items()])
        turn_data = self.once_doc_list_crawler(query_text, crawl_unit, turn_id=1)
        count = turn_data["queryResult"]["resultCount"]
        assert count <= self.crawl_limit
        for turn_id in range(1, math.ceil(count / crawl_unit) + 1):
            if turn_id > 1:
                turn_data = self.once_doc_list_crawler(query_text, crawl_unit, turn_id)
            turn_results = [d["rowkey"] for d in turn_data["queryResult"]["resultList"]]
            assert len(turn_results) > 0
            assert set(turn_results) == set(turn_data["relWenshu"])
            results += turn_results
        assert len(results) == count
        return results

    # crawl detailed article via docId
    # 加入对无法获取的异常文件的处理（获取极少数文件的正文时会持续返回InvalidChunkLength Error, 比如文件"1c9e6f351f8a4d9ca96dab3300909564"）
    def detail_crawler(self, doc_id: str):
        params = {
            'docId': doc_id,  # "a8f0be8fe8914c29a7d2ad53000b03f6"
            'ciphertext': self.ciphertext,
            'cfg': 'com.lawyee.judge.dc.parse.dto.SearchDataDsoDTO@docInfoSearch',
            '__RequestVerificationToken': self.verification_token,
        }
        # 发送请求, 拿到返回结果并解密
        try_count, error = 0, None
        while try_count <= self.max_retry:
            try_count += 1
            try:
                data = self.post(params)
                return self.cracker.decrypt(data["secretKey"], data["result"])
            except Exception as exp:
                time.sleep(1)
                error = exp
        print(f"\nError: {doc_id}\t{error}")
        return None

    # 对给定条件组合下指定字段进行值计数 (年份/关键字/文书类型)
    def update_field_count(self, add_query: Dict[str, str], count_field: str):
        key = self.desc2key[count_field]
        query_text = str([self.base_query] + [{"key": k, "value": v} for k, v in add_query.items()])
        params = {
            'pageId': self.pageId,
            's2': '最高人民法院',
            'groupFields': key,  # 's42' or 's45;s11;s4;s33;s42;s8;s6;s44'
            'queryCondition': query_text,
            'cfg': 'com.lawyee.judge.dc.parse.dto.SearchDataDsoDTO@leftDataItem',
            '__RequestVerificationToken': self.verification_token,
        }
        # 发送请求, 拿到返回结果
        data = self.post(params)
        count_dict = {d["value"]: d["count"] for d in data['result'][key]}
        return count_dict

    # 统计给定条件组合下的结果总数
    def update_total_count(self, add_query: Dict[str, str]):
        query_text = str([self.base_query] + [{"key": k, "value": v} for k, v in add_query.items()])
        data = self.once_doc_list_crawler(query_text)
        return data["queryResult"]["resultCount"]

    # 预处理: 将正文爬虫结果中的docId抽出, 去除无用字段和qwContent值中的HTML标签
    def detail_pro(self, raw: Dict[str, str]):
        new = {}
        for k, v in raw.items():
            if v and k != "s5":
                if k == "qwContent":
                    for s, repl in self.repl_dict.items():
                        v = re.sub(s, repl, v)
                new[k] = v
        return {raw["s5"]: new}

    # LV2条件分流：使用二分法递归产生日期范围, 直至范围内文书总数不超过1k
    def generate_date_queries(self, query: Dict[str, str], start_date: dt, end_date: dt):
        # LV2条件: cprq (裁判日期)
        new_query = query.copy()
        new_query[self.key2] = f"{self.date2str(start_date)} TO {self.date2str(end_date)}"
        total_count = self.update_total_count(new_query)
        if total_count <= self.crawl_limit:
            return [[new_query, total_count]] if total_count else []
        else:
            interval = (end_date - start_date).days
            if interval:
                mid_date = start_date + timedelta(interval // 2)
                return self.generate_date_queries(query, start_date, mid_date) \
                    + self.generate_date_queries(query, mid_date + timedelta(1), end_date)
            else:
                # 引入第三层及以上条件, 解决单法院单日文书数超过1k的爬取问题
                return self.generate_upper_queries(new_query, total_count)

    # LV3/LV4条件分流：对LV2条件不足以实现完全分流的query进一步分流
    def generate_upper_queries(self, query: Dict[str, str], total_count):
        length_list = []
        # LV3条件: s6 (文书类型)
        value_counts = self.update_field_count(query, count_field="doc_type")
        for value, count in value_counts.items():
            new_query = query.copy()
            new_query[self.key3] = value
            if count <= self.crawl_limit:
                length_list += [[new_query, count]]
            else:
                # LV4条件: s7 (案号)
                for i in range(10):
                    new_new_query = new_query.copy()
                    new_new_query[self.key4] = f"行审{i}"
                    count = self.update_total_count(new_new_query)
                    assert count <= self.crawl_limit
                    if count:
                        length_list += [[new_new_query, count]]
        assert total_count == sum(x[1] for x in length_list)
        return length_list

    # Coarse-grained Scheduler to balance payload among processes
    # 性能: 1) 考虑了query长度对进程执行时间的影响, 在每个进程包含的query总长度（即proc_len）上实现了较好的平衡;
    #       2) 未考虑query数量对进程执行时间的影响, 靠后分配的proc的query数量会显著增加;
    #       3) 综合来看, 该预调度算法已经在低复杂度条件下实现了效果相当不错的负载均衡, 适合本项目这种query数量对总爬取时间影响不大的情况。
    def scheduler(self, length_list: List[List[Any]]):
        total_count = self.update_total_count({})
        query_list = [x for x, _ in length_list]
        length_dict = dict(sorted([(i, y) for i, (_, y) in enumerate(length_list)], key=lambda x: x[1], reverse=True))
        print("Query_Lens: ", length_dict, "\n")
        sum_query_count = sum(length_dict.values())
        schedule_list, proc_lens = [[] for _ in range(self.num_workers)], [0] * self.num_workers
        self.proc_unit = sum_query_count / self.num_workers
        for pid in range(self.num_workers - 1):
            # 选length_dict和不超过unit的前k个, k尽可能大
            k, sum_ = 0, 0
            for qid, l in length_dict.items():
                k, sum_ = k + 1, sum_ + l
                if sum_ > self.proc_unit:
                    k, sum_ = k - 1, sum_ - l
                    break
            for qid, l in list(length_dict.items())[:k]:
                length_dict.pop(qid)
                schedule_list[pid].append((qid, query_list[qid], l))
            rest = self.proc_unit - sum_
            proc_lens[pid] = sum_
            # 从剩余length_dict中选abs与rest差最小的
            if length_dict and rest >= 1:
                length_list = list(length_dict.items())
                qid, l = length_list[np.argmin(np.abs(np.array(list(length_dict.values())) - rest))]
                length_dict.pop(qid)
                schedule_list[pid].append((qid, query_list[qid], l))
                proc_lens[pid] = sum_ + l
            if not length_dict:
                break
        schedule_list[self.num_workers - 1] = [(qid, query_list[qid], length) for qid, length in length_dict.items()]
        proc_lens[self.num_workers - 1] = sum(length_dict.values())
        print(f"Scheduler:\nT{total_count}, S{sum_query_count}, P{sum(proc_lens)}")
        # Metrics
        avg_abs = np.mean(np.abs(np.array(proc_lens) - self.proc_unit))
        print("Unit {:.1f}, Avg_ABS {:.1f}, Proc_Lens {}".format(self.proc_unit, avg_abs, proc_lens))
        for pid, schedule in enumerate(schedule_list):
            print(f"[{pid}] L{len(schedule)} {schedule}")
        print()
        return schedule_list, proc_lens

    # Main Proc: Counter
    def proc_counter(self, court_name_list: List[str], pid: int = 0, queue=None):
        proc_length_list = []
        for court_name in court_name_list:
            query = {self.key1: court_name}
            total_count = self.update_total_count(query)
            proc_length_list += [[query, total_count]]
            if queue is not None:
                queue.put([[query, total_count]])
        # print(f"End for {pid}")
        return proc_length_list

    # Main Proc: Generate queries to split dataflow
    def proc_query_generator(self, proc_query_list: List[List[Any]], proc_total_docs: int, pid: int = 0, queue=None):
        proc_length_list, proc_total_loss = [], 0
        for _, query, query_length in proc_query_list:
            year_list = self.update_field_count(query, count_field="year").keys()
            start_date, end_date = dt(int(min(year_list)), 1, 1), dt(int(max(year_list)), 12, 31)
            query_length_list = self.generate_date_queries(query, start_date, end_date)
            query_loss = query_length - sum(x[1] for x in query_length_list)
            if query_loss:
                proc_total_loss += query_loss
                # print(f"Loss: {query_loss} Query: {query}")
            proc_length_list += query_length_list
            if queue is not None:
                queue.put(query_length_list)
        print("\nEND Proc {}, Split Queries {} -> {}, Docs {}, Lost {}"
              .format(pid, len(proc_query_list), len(proc_length_list), proc_total_docs, proc_total_loss))
        return proc_length_list

    # Main Proc: Crawl docId list
    def proc_doc_list_crawler(self, proc_query_list: List[List[Any]], proc_total_docs: int, pid: int = 0, queue=None):
        # Theoretical Patterns: Σ$query_total_docs == $proc_total_docs
        start_t, total_cnt, repl_cnt, proc_doc_indices = time.perf_counter(), 0, 0, []
        for idx, (qid, query, query_total_docs) in enumerate(proc_query_list):
            query_doc_indices = None
            for crawl_unit in self.crawl_units:
                try:
                    query_doc_indices = self.doc_list_crawler(query, crawl_unit)
                    break
                except:
                    continue
            if query_total_docs != len(query_doc_indices):
                print(f"LEN Changed: {query} {query_total_docs} -> {len(query_doc_indices)}")  # 需要在执行III前更新I/II的结果
            proc_doc_indices += query_doc_indices
            if queue is not None:
                queue.put(query_doc_indices)
        # print("\nEND Proc {}, {} queries, {} docs".format(pid, len(proc_query_list), len(proc_doc_indices)))
        return proc_doc_indices

    # Main Proc: Crawl doc detailed info
    def proc_detail_crawler(self, doc_id_list: List[str], pid: int = 0, queue=None):
        proc_doc_dict = {}
        for doc_id in doc_id_list:
            detail_data = self.detail_crawler(doc_id)
            if detail_data is None:  # 处理异常
                if queue is not None:
                    queue.put(None)
                continue
            pro_data = self.detail_pro(detail_data)
            proc_doc_dict.update(pro_data)
            if queue is not None:
                queue.put(pro_data)
        if self.do_split:  # do_split=True则在进程执行结束时保存结果
            data_path = self.args.split_result_path.format(pid)
            dump_data(proc_doc_dict, data_path)
            print("\nEND Proc {}, Saved {} Docs to {}".format(pid, len(proc_doc_dict), data_path))
        else:
            print("\nEND Proc {}, GOT {} Docs".format(pid, len(proc_doc_dict)))
        return proc_doc_dict

    # Merge Split Results
    def merge_results(self, prev_num_workers, num_docs):
        doc_dict = {}
        for pid in trange(prev_num_workers, desc="Merge Split Results"):
            split_data = load_data(self.args.split_result_path.format(pid))
            doc_dict.update(split_data)
        print("GOT {}/{} Doc Details, Lost {}".format(len(doc_dict), num_docs, num_docs - len(doc_dict)))
        dump_data(doc_dict, self.args.result_path)
        return doc_dict  # 返回结果

    # Multi-Process Controller
    def run_crawler(self):
        # 爬取法院列表
        court_names = [court["name"] for court in self.court_list_crawler()]
        # 爬取文书信息
        if self.use_cache and op.exists(self.args.result_path):
                return load_data(self.args.result_path)
        doc_index_list = []
        if self.use_cache and op.exists(self.args.doc_index_path):
            doc_index_list = load_data(self.args.doc_index_path)
        else:
            # 使用分流机制生成组合条件, 获得文书网上的所有行政诉讼文书
            # 共进行4轮请求, 每轮都首先进行粗粒度预调度为每个进程分配query, 然后调用multiprocessing模块实现多进程爬取
            # sample query: {"s2": "北京市高级人民法院", "cprq": "2021-05-01 TO 2021-06-01"}
            if self.use_cache and op.exists(self.args.query_length_path):
                length_list_2 = load_data(self.args.query_length_path)
            else:
                # TODO LIST: 拆分损失评估, 为何会造成76k的拆分损失，能否弄到一个域外数据？从而改进拆分减小损失？
                # Stage I: Schedule + Multi-Proc （统计所有LV1 Query的长度）
                length_list = []
                self.num_queries = len(court_names)
                self.proc_unit = math.ceil(self.num_queries / self.num_workers)
                print(f"[MP Stage I] Workers: {self.num_workers}, Unit: {self.proc_unit}, Queries: {self.num_queries}")
                q = multiprocessing.Queue()
                for pid in range(self.num_workers):
                    proc_court_names = court_names[self.proc_unit * pid: self.proc_unit * (pid + 1)]
                    p = multiprocessing.Process(target=self.proc_counter, args=(proc_court_names, pid, q))
                    p.start()
                for _ in trange(self.num_queries, desc="Count LV1 Queries"):
                    proc_data = q.get()
                    length_list += proc_data
                print("Counted {} courts".format(len(length_list)))
                # Counted 3531 courts in Stage I, 2022-05-31 21:00
                # Stage I: Split （找出所有长度超出1k的LV1 Query）
                length_list_1, length_list_2 = [], []
                for query, total_count in length_list:
                    if total_count <= self.crawl_limit:
                        if total_count:
                            length_list_2 += [[query, total_count]]
                        continue
                    else:
                        length_list_1 += [[query, total_count]]
                # Stage II: Schedule + Multi-Proc （对长度超出1k的LV1 Query使用LV2+条件进一步分流，直至每个query结果长度≤1k）
                self.num_queries = len(length_list_1)
                schedule_list, proc_lens = self.scheduler(length_list_1)
                print(f"[MP Stage II] Workers: {self.num_workers}, Unit: {self.proc_unit}, Queries: {self.num_queries}")
                q = multiprocessing.Queue()
                for pid in range(self.num_workers):
                    p = multiprocessing.Process(target=self.proc_query_generator,
                                                args=(schedule_list[pid], proc_lens[pid], pid, q))
                    p.start()
                for _ in trange(self.num_queries, desc="Split LV2+ Queries"):
                    proc_data = q.get()
                    length_list_2 += proc_data
                total_count = self.update_total_count({})
                sum_query_count = sum(x[1] for x in length_list_2)
                print("GOT {}/{}, Lost {}, Split Queries {}/{} -> {}".
                      format(sum_query_count, total_count, total_count - sum_query_count,
                             len(length_list_1), len(length_list), len(length_list_2)))
                dump_data(length_list_2, self.args.query_length_path)
                # GOT 3063303/3065614, Lost 2311, Split Queries 848/3531 -> 6540 in Stage II, 2022-05-31 21:00

            # Stage III: Schedule + Multi-Proc （爬取文书列表）
            # 数据重复性: 1) s2字段本身存在值重复, 如"新绛县人民法院"和"绛县人民法院";
            #            2) 同一文书同时出现在多个法院的检索结果中（文书6581ace6b24749cf9ffdad1201855f28同时出现在"洪洞县人民法院"和"新绛县人民法院"的结果中）。
            self.num_queries = len(length_list_2)
            schedule_list, proc_lens = self.scheduler(length_list_2)
            print(f"[MP Stage III] Workers: {self.num_workers}, Unit: {self.proc_unit}, Queries: {self.num_queries}")
            q = multiprocessing.Queue()
            for pid in range(self.num_workers):
                p = multiprocessing.Process(target=self.proc_doc_list_crawler,
                                            args=(schedule_list[pid], proc_lens[pid], pid, q))
                p.start()
            for _ in trange(self.num_queries, desc="Crawl Doc Indices"):
                proc_data = q.get()
                doc_index_list += proc_data
            raw_num_docs = len(doc_index_list)
            doc_index_list = list(set(doc_index_list))
            num_docs = len(doc_index_list)
            print("GOT {}/{} Doc Indices, Repl {}".format(num_docs, raw_num_docs, raw_num_docs - num_docs))
            dump_data(doc_index_list, self.args.doc_index_path)
            # GOT 2989757/3063303 Doc Indices, Repl 73546 in Stage III, 2022-05-31 21:00

        # 加载前分块结果（如果有）
        self.num_docs = len(doc_index_list)
        if self.use_cache:
            split_files = sorted(os.listdir(self.args.split_dir), key=lambda x: int(re.findall(r'\d+', x)[0]))
            if split_files:
                assert len(split_files) == int(re.findall(r'\d+', split_files[-1])[0]) + 1  # 检查是否有文件缺失
                return self.merge_results(len(split_files), self.num_docs)

        # Stage IV: Schedule + Multi-Proc （爬取文书正文）
        # 运行说明: 
        # 1) 远程运行: 目前手机端文书网反爬只检查cookie, 不检查ip, 故可先在本地重置headers, 然后在服务器上运行（服务器上无UI, 不能开selenium登录）;
        # 2) 运行时长: Stage IV在服务器上可以开到80个进程, 此时速度最快, 约300/s, 2.9h左右即可爬完3M条;
        # 2) 分块存储: 防止结果太大存不下, 采用分块存储, 最后再合并;
        # 3) 错误修复: 获取极少数文书的正文时会持续返回InvalidChunkLength Error, 比如文书"1c9e6f351f8a4d9ca96dab3300909564", 
        #             已引入后期增补机制0对上述第一波爬取时出现Error的文书进行重新爬取或替换, 参见supplement.py。
        self.proc_unit = math.ceil(self.num_docs / self.num_workers)
        print(f"[MP Stage IV] Workers: {self.num_workers}, Unit: {self.proc_unit}, Docs: {self.num_docs}")
        q = multiprocessing.Queue()
        for pid in range(self.num_workers):
            proc_doc_indices = doc_index_list[self.proc_unit * pid: self.proc_unit * (pid + 1)]
            p = multiprocessing.Process(target=self.proc_detail_crawler, args=(proc_doc_indices, pid, q))
            p.start()
        if self.do_split:  # 默认分块存储
            for _ in trange(self.num_docs, desc="Crawl Doc Details"):
                __ = q.get()
            return None
        else:
            doc_dict = {}
            for _ in trange(self.num_docs, desc="Crawl Doc Details"):
                detail_data = q.get()
                if detail_data is not None:
                    doc_dict.update(detail_data)
            print("GOT {}/{} Doc Details, Lost {}".format(len(doc_dict), self.num_docs, self.num_docs - len(doc_dict)))
            dump_data(doc_dict, self.args.result_path)
            return doc_dict  # 返回结果
            # GOT 2989754/2989757 Doc Details, Lost 3 in Stage IV, 2022-06-01 05:00


if __name__ == '__main__':
    args = Config()
    crawler = WenShuCrawler(args)
    crawler.run_crawler()
