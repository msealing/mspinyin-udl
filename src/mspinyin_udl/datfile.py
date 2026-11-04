# -*- coding: utf-8 -*-
"""解析微软拼音导出的私有词库文件。

支持两种文件（都是定长 60 字节记录 + 文件头）：

* ``ChsPinyinUDL.dat``（词库和自学习 → 导出词库）
    文件头 9216 字节；记录里带「汉字 + 每字音节序号」，因此能还原拼音。
* ``ChsPinyinIH.dat``（输入历史）
    文件头 5120 字节；记录里只有汉字，没有音节序号。

格式是逆向出来的，未公开；本模块对异常记录做严格校验并跳过，
不会因为个别坏块而中断整个文件。
"""
from __future__ import annotations

import struct
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple

from .syllables import SYLLABLE_COUNT, SYLLABLE_TABLE

BLOCK_SIZE = 60
HEADER_UDL = 9216
HEADER_IH = 5120

# 记录内的字段偏移
UDL_LEN_OFFSET = 10
UDL_MARKER_OFFSET = 11
UDL_MARKER = 0x5A
TEXT_OFFSET = 12

MAX_CHARS_UDL = (BLOCK_SIZE - TEXT_OFFSET) // 4      # 带音节序号，最多 12 字
MAX_CHARS_IH = (BLOCK_SIZE - TEXT_OFFSET) // 2       # 无音节序号，最多 24 字


@dataclass(frozen=True)
class Entry:
    """一个词条。"""

    text: str
    syllable_ids: Tuple[int, ...] = ()
    source: str = ""

    @property
    def syllables(self) -> Tuple[str, ...]:
        return tuple(SYLLABLE_TABLE[i] for i in self.syllable_ids)

    @property
    def pinyin(self) -> str:
        return " ".join(self.syllables)

    @property
    def pinyin_joined(self) -> str:
        return "".join(self.syllables)

    @property
    def has_pinyin(self) -> bool:
        return bool(self.syllable_ids)


@dataclass
class ParseReport:
    path: str = ""
    layout: str = ""
    header_size: int = 0
    blocks: int = 0
    entries: int = 0
    skipped: int = 0
    reasons: dict = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {
            "path": self.path,
            "layout": self.layout,
            "header_size": self.header_size,
            "blocks": self.blocks,
            "entries": self.entries,
            "skipped": self.skipped,
            "skip_reasons": dict(self.reasons),
        }


def _decode_text(raw: bytes) -> str:
    try:
        text = raw.decode("utf-16le")
    except UnicodeDecodeError:
        return ""
    if "\x00" in text:
        return ""
    if any(ord(c) < 0x20 for c in text):
        return ""
    return text


def _parse_udl(body: bytes, report: ParseReport) -> List[Entry]:
    entries: List[Entry] = []
    index = 1
    total = len(body) // BLOCK_SIZE
    while index <= total:
        base = index * BLOCK_SIZE
        index += 1
        report.blocks += 1
        if base + BLOCK_SIZE > len(body):
            break
        length = body[base + UDL_LEN_OFFSET]
        if length < 1 or length > MAX_CHARS_UDL:
            report.skipped += 1
            report.reasons["bad_length"] = report.reasons.get("bad_length", 0) + 1
            continue
        if body[base + UDL_MARKER_OFFSET] != UDL_MARKER:
            report.skipped += 1
            report.reasons["bad_marker"] = report.reasons.get("bad_marker", 0) + 1
            continue
        start = base + TEXT_OFFSET
        end = start + length * 2
        if end + length * 2 > base + BLOCK_SIZE:
            report.skipped += 1
            report.reasons["overflow"] = report.reasons.get("overflow", 0) + 1
            continue
        text = _decode_text(body[start:end])
        if not text or len(text) != length:
            report.skipped += 1
            report.reasons["bad_text"] = report.reasons.get("bad_text", 0) + 1
            continue
        ids = struct.unpack_from("<%dH" % length, body, end)
        if any(i >= SYLLABLE_COUNT for i in ids):
            report.skipped += 1
            report.reasons["bad_syllable"] = report.reasons.get("bad_syllable", 0) + 1
            continue
        entries.append(Entry(text=text, syllable_ids=tuple(ids)))
    report.entries = len(entries)
    return entries


def _parse_ih(body: bytes, report: ParseReport) -> List[Entry]:
    entries: List[Entry] = []
    index = 1
    total = len(body) // BLOCK_SIZE
    while index <= total:
        base = index * BLOCK_SIZE
        index += 1
        report.blocks += 1
        if base + BLOCK_SIZE > len(body):
            break
        length = body[base]
        if length < 1 or length > MAX_CHARS_IH:
            report.skipped += 1
            report.reasons["bad_length"] = report.reasons.get("bad_length", 0) + 1
            continue
        start = base + TEXT_OFFSET
        end = start + length * 2
        if end > base + BLOCK_SIZE:
            report.skipped += 1
            report.reasons["overflow"] = report.reasons.get("overflow", 0) + 1
            continue
        text = _decode_text(body[start:end])
        if not text or len(text) != length:
            report.skipped += 1
            report.reasons["bad_text"] = report.reasons.get("bad_text", 0) + 1
            continue
        entries.append(Entry(text=text))
    report.entries = len(entries)
    return entries


def sniff_layout(name: str, body: bytes) -> str:
    """猜测是 UDL 还是 IH。"""
    lowered = name.lower()
    if "udl" in lowered:
        return "udl"
    if "ih" in lowered:
        return "ih"

    def score(layout: str) -> float:
        rep = ParseReport()
        entries = _parse_udl(body, rep) if layout == "udl" else _parse_ih(body, rep)
        if rep.blocks == 0:
            return 0.0
        return len(entries) / max(rep.blocks, 1)

    return "udl" if score("udl") >= score("ih") else "ih"


def read_dat(
    path: str | Path,
    layout: str = "auto",
    header_size: int | None = None,
) -> Tuple[List[Entry], ParseReport]:
    """读取一个 .dat，返回 (词条列表, 解析报告)。"""
    path = Path(path)
    data = path.read_bytes()
    name = path.name
    if layout == "auto":
        layout = sniff_layout(name, data)

    if header_size is None:
        header_size = HEADER_IH if layout == "ih" else HEADER_UDL

    if len(data) <= header_size:
        raise ValueError(
            "%s 文件只有 %d 字节，不足文件头长度 %d；如果这是别的版本导出的文件，"
            "试下 --header 参数。" % (path, len(data), header_size)
        )

    report = ParseReport(path=str(path), layout=layout, header_size=header_size)
    body = data[header_size:]
    entries = _parse_udl(body, report) if layout == "udl" else _parse_ih(body, report)
    return entries, report


def read_many(paths: Iterable[str | Path], layout: str = "auto") -> Tuple[List[Entry], List[ParseReport]]:
    """读取多个文件，按「词 + 拼音」去重合并。"""
    merged: List[Entry] = []
    seen = set()
    reports: List[ParseReport] = []
    for p in paths:
        entries, report = read_dat(p, layout=layout)
        reports.append(report)
        for entry in entries:
            key = (entry.text, entry.syllable_ids)
            if key in seen:
                continue
            seen.add(key)
            merged.append(entry)
    return merged, reports
