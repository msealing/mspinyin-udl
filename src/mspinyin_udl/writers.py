# -*- coding: utf-8 -*-
"""各种输出格式。

每个 writer 的签名统一为 ``writer(entries, path, options) -> int``，
返回实际写出的条数。想加新格式，写一个函数再注册到 ``WRITERS`` 即可。
"""
from __future__ import annotations

import contextlib
import csv
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional, Sequence

WEIGHT_DEFAULT = 100


@dataclass
class WriterOptions:
    name: str = "dict"
    weight: int = WEIGHT_DEFAULT
    sep: str = " "                 # 拼音音节分隔符（spaced 风格）
    joined: bool = False           # True = 拼音连写（nihao）
    ms_position: int = 1           # 微软自定义短语的固定候选位置 1..9
    template: str = ""             # template 格式的模板
    encoding: str = "utf-8"
    eol: str = "\n"


def _pinyin(entry, options: WriterOptions) -> str:
    if options.joined:
        return entry.pinyin_joined
    return options.sep.join(entry.syllables)


@contextlib.contextmanager
def _open(path: Optional[Path], options: WriterOptions, newline: Optional[str] = None):
    """打开输出；``path=None`` 表示写标准输出（--stdout）。"""
    if path is None:
        yield sys.stdout
        return
    handle = open(path, "w", encoding=options.encoding,
                  newline=options.eol if newline is None else newline)
    try:
        yield handle
    finally:
        handle.close()


def _iter_rows(entries: Iterable, options: WriterOptions) -> Iterable[tuple]:
    for index, entry in enumerate(entries, 1):
        yield index, entry, _pinyin(entry, options)


# --------------------------------------------------------------------------- #
# Rime（小狼毫 / 鼠须管 / 同文 / fcitx5-rime）
# --------------------------------------------------------------------------- #
def write_rime(entries, path: Path, options: WriterOptions) -> int:
    count = 0
    with _open(path, options) as fh:
        fh.write("# Rime 词典，由微软拼音词库转换（mspinyin-udl）\n")
        fh.write("---\n")
        fh.write("name: %s\n" % options.name)
        fh.write('version: "1.0"\n')
        fh.write("sort: by_weight\n")
        fh.write("columns:\n  - text\n  - code\n  - weight\n")
        fh.write("...\n")
        for _, entry, pinyin in _iter_rows(entries, options):
            if not pinyin:
                continue
            fh.write("%s\t%s\t%d\n" % (entry.text, pinyin, options.weight))
            count += 1
    return count


# --------------------------------------------------------------------------- #
# 通用文本表
# --------------------------------------------------------------------------- #
def write_tsv(entries, path: Path, options: WriterOptions) -> int:
    count = 0
    with _open(path, options) as fh:
        fh.write("# 词\t拼音\t词频\n")
        for _, entry, pinyin in _iter_rows(entries, options):
            fh.write("%s\t%s\t%d\n" % (entry.text, pinyin, options.weight))
            count += 1
    return count


def write_txt(entries, path: Path, options: WriterOptions) -> int:
    count = 0
    with _open(path, options) as fh:
        for _, entry, pinyin in _iter_rows(entries, options):
            if pinyin:
                fh.write("%s\t%s\n" % (entry.text, pinyin))
            else:
                fh.write("%s\n" % entry.text)
            count += 1
    return count


def write_csv(entries, path: Path, options: WriterOptions) -> int:
    count = 0
    with _open(path, options, newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["text", "pinyin", "weight"])
        for _, entry, pinyin in _iter_rows(entries, options):
            writer.writerow([entry.text, pinyin, options.weight])
            count += 1
    return count


def write_json(entries, path: Path, options: WriterOptions) -> int:
    rows = []
    for _, entry, pinyin in _iter_rows(entries, options):
        rows.append(
            {
                "text": entry.text,
                "pinyin": pinyin,
                "syllables": list(entry.syllables),
                "weight": options.weight,
            }
        )
    with _open(path, options) as fh:
        json.dump(rows, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    return len(rows)


def write_words(entries, path: Path, options: WriterOptions) -> int:
    """每行一个词，不带拼音（给会自己推读音的输入法/工具用）。"""
    count = 0
    with _open(path, options) as fh:
        for entry in entries:
            fh.write("%s\n" % entry.text)
            count += 1
    return count


# --------------------------------------------------------------------------- #
# 微软拼音「用户自定义短语」导入格式
# --------------------------------------------------------------------------- #
def write_ms_phrase(entries, path: Path, options: WriterOptions) -> int:
    """格式：``拼音码,位置,短语``，位置是候选里的序号（1..9）。

    在「设置 → 词库和自学习 → 用户自定义短语 → 导入」里使用。
    没有拼音的词条会跳过（这个格式必须要编码）。
    """
    position = max(1, min(9, int(options.ms_position)))
    count = 0
    with _open(path, options) as fh:
        for entry in entries:
            if not entry.has_pinyin:
                continue
            fh.write("%s,%d,%s\n" % (entry.pinyin_joined, position, entry.text))
            count += 1
    return count


# --------------------------------------------------------------------------- #
# 自定义模板
# --------------------------------------------------------------------------- #
def write_template(entries, path: Path, options: WriterOptions) -> int:
    if not options.template:
        raise ValueError("template 格式需要 --template，例如 --template '{text}\\t{pinyin}'")
    count = 0
    with _open(path, options) as fh:
        for index, entry, pinyin in _iter_rows(entries, options):
            line = (
                options.template
                .replace("{index}", str(index))
                .replace("{text}", entry.text)
                .replace("{word}", entry.text)
                .replace("{pinyin}", pinyin)
                .replace("{pinyin_joined}", entry.pinyin_joined)
                .replace("{weight}", str(options.weight))
                .replace("\\t", "\t")
                .replace("\\n", "\n")
            )
            fh.write(line + ("\n" if not line.endswith("\n") else ""))
            count += 1
    return count


@dataclass(frozen=True)
class Format:
    name: str
    extension: str
    description: str
    writer: Callable


WRITERS: Dict[str, Format] = {
    "rime": Format("rime", ".dict.yaml", "Rime 词典（text / code / weight）", write_rime),
    "tsv": Format("tsv", ".tsv", "词\\t拼音\\t词频", write_tsv),
    "txt": Format("txt", ".txt", "词\\t拼音", write_txt),
    "csv": Format("csv", ".csv", "CSV（text, pinyin, weight）", write_csv),
    "json": Format("json", ".json", "JSON 数组，含音节拆分", write_json),
    "words": Format("words", ".words.txt", "每行一个词（无拼音）", write_words),
    "ms-phrase": Format("ms-phrase", ".ms-phrase.txt", "微软拼音自定义短语（拼音码,位置,短语）", write_ms_phrase),
    "template": Format("template", ".txt", "按 --template 自定义", write_template),
}

FORMAT_ALIASES = {
    "yaml": "rime",
    "dict.yaml": "rime",
    "text": "txt",
    "word": "words",
    "wordlist": "words",
    "microsoft": "ms-phrase",
    "ms": "ms-phrase",
    "custom": "template",
}


def resolve_formats(spec: str) -> List[str]:
    """把 ``"all"`` 或 ``"rime,tsv"`` 解析成格式名列表。"""
    spec = (spec or "").strip()
    if not spec:
        return ["rime", "tsv"]
    if spec.lower() == "all":
        # template 是自定义格式，必须给 --template 才有意义，不放进 all
        return [name for name in WRITERS if name != "template"]
    names = []
    for raw in spec.split(","):
        name = raw.strip().lower()
        if not name:
            continue
        name = FORMAT_ALIASES.get(name, name)
        if name not in WRITERS:
            raise ValueError("未知格式: %s（可用: %s）" % (raw.strip(), ", ".join(WRITERS)))
        names.append(name)
    return names


def write_format(
    name: str,
    entries: Sequence,
    path: Optional[Path],
    options: WriterOptions,
) -> int:
    """写出一种格式；``path=None`` 表示写到标准输出。"""
    fmt = WRITERS[name]
    if path is not None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
    return fmt.writer(entries, path, options)
