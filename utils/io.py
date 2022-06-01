# 数据加载和保存统一接口
import ujson
from typing import Any


# 加载数据
def load_data(path: str):
    return ujson.load(open(path, encoding="utf-8"))


# 缓存数据
def dump_data(data: Any, path: str):
    ujson.dump(data, open(path, "w+", encoding="utf-8"), ensure_ascii=False, indent=4)
