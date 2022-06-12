# 将增补结果合并, 并测试使用pandas进行数据加载（压力测试）
import os
import re

import pandas as pd
from tqdm import trange, tqdm
from config import Config
from utils import load_data, dump_data


# Update result & Convert to List
def merge_results(args: Config):
    doc_dict = load_data(args.result_path)
    num_docs = len(doc_dict)
    # update result
    sup_files = sorted(os.listdir(args.sup_dir), key=lambda x: int(re.findall(r'\d+', x)[0]))
    if sup_files:
        assert len(sup_files) == int(re.findall(r'\d+', sup_files[-1])[0]) + 1  # 检查是否有文件缺失
        for sid in trange(len(sup_files), desc="Merge Sup Results"):
            sup_data = load_data(args.sup_result_path.format(sid))
            doc_dict.update(sup_data)
        dump_data(doc_dict, args.result_path)
        print("GOT {}/{} Doc Details, Add {} Sups".format(len(doc_dict), num_docs, len(doc_dict) - num_docs))
    # convert dict to list for pandas
    processed_list = []
    for doc_id, info_dict in tqdm(doc_dict.items(), desc="Convert Dict to List"):
        assert "id" not in info_dict
        info_dict["id"] = doc_id
        processed_list.append(info_dict)
    dump_data(processed_list, args.processed_path)
    return processed_list


if __name__ == "__main__":
    args = Config()
    processed_list = merge_results(args)
    df = pd.read_json(args.processed_path)
