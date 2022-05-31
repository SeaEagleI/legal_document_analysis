# 基于对JS的逆向工程, 实现对POST请求参数的构造和对响应结果的解密
import ujson
import random
import time

from typing import Any
from Crypto.Cipher import DES3
from base64 import b64decode, b64encode

# base common params
pageId_size = 32
randStr_size = 24
hex_chars = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'a', 'b', 'c', 'd', 'e', 'f']
alnum_chars = [
    '0', '1', '2', '3', '4', '5', '6', '7', '8', '9',
    'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w',
    'x', 'y', 'z',
    'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W',
    'X', 'Y', 'Z',
]


# 对请求参数加密, 对响应参数解密
class DES3_Cracker:
    def __init__(self):
        self.block_size = 8
        self.iv = time.strftime("%Y%m%d", time.localtime()).encode()

    def pad(self, s):
        return s + (self.block_size - len(s) % self.block_size) * chr(self.block_size - len(s) % self.block_size)

    def unpad(self, s):
        return s[:-ord(s[len(s) - 1:])]

    # DES3-CBC方式加密 (对请求参数)
    def encrypt(self, key, raw):
        raw = self.pad(raw)
        _cipher = DES3.new(key, DES3.MODE_CBC, IV=self.iv)
        return b64encode(_cipher.encrypt(raw.encode()))

    # DES3-CBC方式解密 (对响应参数)
    def decrypt(self, key, enc):
        enc = b64decode(enc)
        _cipher = DES3.new(key, DES3.MODE_CBC, IV=self.iv)
        return ujson.loads(self.unpad(_cipher.decrypt(enc)).decode('utf-8'))


# 生成POST请求参数中的pageId
def uuid():
    return "".join([random.choice(hex_chars) for _ in range(pageId_size)])


# 生成POST请求参数中的ciphertext.salt和__RequestVerificationToken
def rand_str():
    return "".join([random.choice(alnum_chars) for _ in range(randStr_size)])


# 生成POST请求参数中的ciphertext
def cipher():
    salt = rand_str()
    timestamp = str(time.time()).replace('.', '')[:13]
    iv = time.strftime("%Y%m%d", time.localtime())
    enc = DES3_Cracker().encrypt(salt, timestamp).decode()
    return " ".join([str(bin(ord(c))[2:]) for c in salt + iv + enc])  # str2bin


# 加载数据
def load_data(path: str):
    return ujson.load(open(path, encoding="utf-8"))


# 缓存数据
def dump_data(data: Any, path: str):
    ujson.dump(data, open(path, "w+", encoding="utf-8"), ensure_ascii=False, indent=4)
