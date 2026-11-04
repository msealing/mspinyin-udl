# -*- coding: utf-8 -*-
"""生成**假的** ChsPinyinUDL.dat / ChsPinyinIH.dat（测试与演示用）。

不含任何人的真实词库。命令行用法见 ``tools/make_sample_dat.py``。

>>> from mspinyin_udl.testing import build_udl
>>> open("sample.dat", "wb").write(build_udl())
"""
from __future__ import annotations

import struct
from typing import Sequence, Tuple

from .syllables import SYLLABLE_TABLE

BLOCK_SIZE = 60
HEADER_UDL = 9216
HEADER_IH = 5120

# 真实文件头开头 24 字节（其余补 0；解析时整个文件头都会被跳过）
UDL_HEAD_PREFIX = bytes.fromhex("55AA88810200600055AA55AA0C4000000000000036877D32")

DEFAULT_SAMPLES: Tuple[Tuple[str, str], ...] = (
    ("中国", "zhong guo"),
    ("你好", "ni hao"),
    ("重庆", "chong qing"),
    ("银行", "yin hang"),
    ("作战计划", "zuo zhan ji hua"),
    ("角色", "jue se"),
    ("处理", "chu li"),
    ("音乐", "yin yue"),
    ("进行数据分析", "jin xing shu ju fen xi"),
    ("阿达哒哒哒", "a da da da da"),   # 默认会被噪声过滤器去掉
)

_TABLE_INDEX = {s: i for i, s in enumerate(SYLLABLE_TABLE)}


def syllable_ids(pinyin: str) -> list:
    out = []
    for s in pinyin.split():
        if s not in _TABLE_INDEX:
            raise ValueError("音节表里没有 %r" % s)
        out.append(_TABLE_INDEX[s])
    return out


def udl_block(word: str, pinyin: str) -> bytes:
    ids = syllable_ids(pinyin)
    if len(ids) != len(word):
        raise ValueError("%s 的拼音音节数(%d)与字数(%d)不一致" % (word, len(ids), len(word)))
    if len(word) > 12:
        raise ValueError("%s 太长，UDL 单条最多 12 字" % word)
    buf = bytearray(BLOCK_SIZE)
    initials = "".join(s[0] for s in pinyin.split())[:3].encode("ascii")
    buf[4:4 + len(initials)] = initials
    buf[8:10] = b"\x00\x04"
    buf[10] = len(word)
    buf[11] = 0x5A
    text = word.encode("utf-16le")
    buf[12:12 + len(text)] = text
    struct.pack_into("<%dH" % len(ids), buf, 12 + len(text), *ids)
    return bytes(buf)


def ih_block(word: str) -> bytes:
    if len(word) > 24:
        raise ValueError("%s 太长，IH 单条最多 24 字" % word)
    buf = bytearray(BLOCK_SIZE)
    buf[0] = len(word)
    text = word.encode("utf-16le")
    buf[12:12 + len(text)] = text
    return bytes(buf)


def build_udl(samples: Sequence[Tuple[str, str]] = DEFAULT_SAMPLES) -> bytes:
    header = bytearray(HEADER_UDL)
    header[: len(UDL_HEAD_PREFIX)] = UDL_HEAD_PREFIX
    rest = b"".join(udl_block(word, pinyin) for word, pinyin in samples)
    return bytes(header) + bytes(BLOCK_SIZE) + rest


def build_ih(samples: Sequence[str] = None) -> bytes:
    if samples is None:
        samples = [word for word, _ in DEFAULT_SAMPLES]
    header = bytearray(HEADER_IH)
    rest = b"".join(ih_block(word) for word in samples)
    return bytes(header) + bytes(BLOCK_SIZE) + rest
