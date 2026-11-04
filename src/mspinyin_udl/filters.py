# -*- coding: utf-8 -*-
"""词条过滤：去掉测试性词条、去重、按字数筛选。"""
from __future__ import annotations

import itertools
from dataclasses import dataclass
from typing import Iterable, List, Sequence

# 微软拼音「自学习」常把这些字学下来：用户敲单字母试输入时，候选第一页就是它们
DEFAULT_NOISE_CHARS = "啊哒顶哇饿"


@dataclass
class FilterOptions:
    keep_noisy: bool = False          # True = 不过滤（--all）
    noise_chars: str = DEFAULT_NOISE_CHARS
    max_repeat: int = 3               # 同一字符连续 >= 3 次视为噪声
    min_chars: int = 1
    max_chars: int = 0                # 0 = 不限制
    dedupe: bool = True               # 按「词」去重，保留先出现的读音
    dedupe_pinyin: bool = False       # True = 按「词 + 拼音」去重


def max_char_run(text: str) -> int:
    if not text:
        return 0
    return max(len(list(group)) for _, group in itertools.groupby(text))


def is_noisy(text: str, noise_chars: str = DEFAULT_NOISE_CHARS, max_repeat: int = 3) -> bool:
    if any(ch in noise_chars for ch in text):
        return True
    return max_char_run(text) >= max_repeat


def apply(
    entries: Iterable,
    options: FilterOptions | None = None,
) -> List:
    """过滤并去重，返回新列表。"""
    opts = options or FilterOptions()
    out: List = []
    seen = set()
    for entry in entries:
        text = entry.text
        length = len(text)
        if length < opts.min_chars:
            continue
        if opts.max_chars and length > opts.max_chars:
            continue
        if not opts.keep_noisy and is_noisy(text, opts.noise_chars, opts.max_repeat):
            continue
        key = (text, entry.syllable_ids) if opts.dedupe_pinyin else text
        if opts.dedupe:
            if key in seen:
                continue
            seen.add(key)
        out.append(entry)
    return out


def summarize(entries: Sequence, label: str = "") -> str:
    lengths = {}
    for entry in entries:
        lengths[len(entry.text)] = lengths.get(len(entry.text), 0) + 1
    hist = " ".join("%d字:%d" % (k, lengths[k]) for k in sorted(lengths))
    prefix = (label + " ") if label else ""
    return "%s共 %d 条（%s）" % (prefix, len(entries), hist)
