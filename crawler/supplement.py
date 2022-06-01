from typing import Dict, Any

from crawler import WenShuCrawler
from config import Config
from utils import dump_data, load_data


# Preprocess for Basic data
def basic_pro(raw: Dict[str, Any]):
    # basic_info -> detail_info 格式所需要的替换值字典
    value_dict = {
        "s9": {  # 数字代码替换为文字
            "0401": "行政一审",
            "0402": "行政二审",
        },
        # "s10": {},  # 数字代码替换为文字
        # "s1": {},  # 去除HTML标签
        # "s26": {},  # 去除HTML标签
    }
    return {k: value_dict[k][v] if k in value_dict else v for k, v in raw.items() if v}


# Supplement_0: Re-process & Pad Error Docs
# ErrMsg: "Connection broken: InvalidChunkLength(got length b'', 0 bytes read)"
def add_0(args: Config, error_indices, basic_dict: Dict[str, Dict[str, Any]]):
    crawler = WenShuCrawler(args)
    res_dict = {}
    for doc_id in error_indices:
        detail_data = crawler.detail_crawler(doc_id)
        if detail_data is None:  # 处理异常
            if doc_id in basic_dict:
                detail_data = {doc_id: basic_pro(basic_dict[doc_id])}
                print(f"Padding for {doc_id}")
            else:
                continue
        else:
            detail_data = crawler.detail_pro(detail_data)
        res_dict.update(detail_data)
    dump_data(res_dict, args.sup_result_path.format(0))
    print("SUP#0: GOT {}/{} Docs".format(len(res_dict), len(error_indices)))


if __name__ == "__main__":
    args = Config()
    args.do_split = False
    basic_dict = load_data(args.basic_result_path)

    # Stage IV损失的3个doc作为第一波增补存入supplement/detail_0
    err_doc_indices = [
        "7ef5f3d9164e459ea631ab3000b8cf3a",
        "1c9e6f351f8a4d9ca96dab3300909564",
        "670658ba34dc4f4cad23a72900f58fdf",
    ]
    add_0(args, err_doc_indices, basic_dict)


