# -*- coding: utf-8 -*-
"""命令行入口。"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List

from . import __version__
from .datfile import read_dat, read_many
from .filters import FilterOptions, apply, summarize
from .writers import WRITERS, WriterOptions, resolve_formats, write_format

EPILOG = """示例：
  mspinyin-udl ChsPinyinUDL.dat                    # 输出 Rime 词典 + TSV
  mspinyin-udl ChsPinyinUDL.dat -f all -o out      # 输出全部格式
  mspinyin-udl ChsPinyinUDL.dat -f rime --noisy    # 保留测试性词条
  mspinyin-udl ChsPinyinIH.dat -f words            # 输入历史（只有词，没有拼音）
  mspinyin-udl A.dat B.dat -f tsv --name merged    # 合并两个文件
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mspinyin-udl",
        description="把微软拼音导出的私有词库（ChsPinyinUDL.dat / ChsPinyinIH.dat）"
                    "转换成 Rime、通用文本、微软自定义短语等多种格式。",
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("inputs", nargs="*", help="一个或多个 .dat 文件")
    parser.add_argument("-f", "--format", default="rime,tsv",
                        help="输出格式，逗号分隔或 all（默认 rime,tsv；--list-formats 看全部）")
    parser.add_argument("-o", "--out", default="out", help="输出目录（默认 out）")
    parser.add_argument("-n", "--name", default="", help="输出文件名（默认取源文件名）")
    parser.add_argument("--sep", default=" ", help="拼音音节分隔符（默认空格）")
    parser.add_argument("--joined", action="store_true", help="拼音连写（nihao，而不是 ni hao）")
    parser.add_argument("--weight", type=int, default=100, help="词频列取值（默认 100）")
    parser.add_argument("--noisy", "--all", dest="keep_noisy", action="store_true",
                        help="保留测试性词条（默认过滤「啊啊啊」「阿达哒哒哒」这类）")
    parser.add_argument("--noise-chars", default=None, help="自定义噪声字集合")
    parser.add_argument("--max-repeat", type=int, default=3, help="同字连续多少次算噪声（默认 3）")
    parser.add_argument("--min-chars", type=int, default=1, help="最短词长（默认 1）")
    parser.add_argument("--max-chars", type=int, default=0, help="最长词长（默认不限）")
    parser.add_argument("--keep-duplicates", action="store_true", help="不去重")
    parser.add_argument("--dedupe-pinyin", action="store_true",
                        help="按「词 + 拼音」去重（默认只按词）")
    parser.add_argument("--ms-position", type=int, default=1, help="ms-phrase 的候选位置 1..9（默认 1）")
    parser.add_argument("--template", default="",
                        help="template 格式的模板，占位符 {text} {pinyin} {pinyin_joined} {weight} {index}")
    parser.add_argument("--encoding", default="utf-8", help="输出编码（默认 utf-8）")
    parser.add_argument("--layout", choices=["auto", "udl", "ih"], default="auto",
                        help="文件类型（默认按文件名/内容判断）")
    parser.add_argument("--header", type=int, default=None,
                        help="手动指定文件头长度（默认 UDL=9216，IH=5120）")
    parser.add_argument("--stats", action="store_true", help="打印解析与过滤统计")
    parser.add_argument("--stdout", action="store_true", help="输出到标准输出（只允许一种格式）")
    parser.add_argument("--list-formats", action="store_true", help="列出所有输出格式")
    parser.add_argument("-V", "--version", action="version", version="mspinyin-udl " + __version__)
    return parser


def _print_formats() -> None:
    print("可用格式：")
    for name, fmt in WRITERS.items():
        print("  %-10s %-12s %s" % (name, fmt.extension, fmt.description))


def _resolve_name(args, inputs: List[Path]) -> str:
    if args.name:
        return args.name
    if len(inputs) == 1:
        stem = inputs[0].name
        for suffix in (".dat", ".DAT"):
            if stem.endswith(suffix):
                stem = stem[: -len(suffix)]
        return stem or "dict"
    return "merged"


def _safe_console() -> None:
    """控制台编码不支持中文时（如英文 Windows 的 cp1252）改成替换而不是崩溃。"""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(errors="replace")  # type: ignore[attr-defined]
        except (AttributeError, ValueError, OSError):
            pass


def main(argv: List[str] | None = None) -> int:
    _safe_console()
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.list_formats:
        _print_formats()
        return 0

    if not args.inputs:
        parser.print_help()
        return 2

    inputs = [Path(p) for p in args.inputs]
    missing = [p for p in inputs if not p.is_file()]
    if missing:
        for p in missing:
            print("找不到文件：%s" % p, file=sys.stderr)
        return 1

    try:
        formats = resolve_formats(args.format)
    except ValueError as exc:
        print(exc, file=sys.stderr)
        return 1
    if args.stdout and len(formats) > 1:
        print("--stdout 只能配合单一格式使用，例如 -f rime。", file=sys.stderr)
        return 1

    # 解析
    try:
        if len(inputs) == 1:
            entries, report = read_dat(inputs[0], layout=args.layout, header_size=args.header)
            reports = [report]
        else:
            entries, reports = read_many(inputs, layout=args.layout)
    except (ValueError, OSError) as exc:
        print("解析失败：%s" % exc, file=sys.stderr)
        return 1

    if not entries:
        print("没有解析出任何词条。确认输入是微软拼音导出的 ChsPinyinUDL*.dat / ChsPinyinIH*.dat；"
              "如果文件被别的版本加密或改了布局，可以用 --header 手动指定文件头长度。", file=sys.stderr)
        return 1

    # 过滤
    filter_opts = FilterOptions(
        keep_noisy=args.keep_noisy,
        noise_chars=args.noise_chars if args.noise_chars is not None else FilterOptions.noise_chars,
        max_repeat=args.max_repeat,
        min_chars=args.min_chars,
        max_chars=args.max_chars,
        dedupe=not args.keep_duplicates,
        dedupe_pinyin=args.dedupe_pinyin,
    )
    selected = apply(entries, filter_opts)

    # 写出
    name = _resolve_name(args, inputs)
    writer_opts = WriterOptions(
        name=name,
        weight=args.weight,
        sep=args.sep,
        joined=args.joined,
        ms_position=args.ms_position,
        template=args.template,
        encoding=args.encoding,
    )

    written = []
    if args.stdout:
        fmt = formats[0]
        count = write_format(fmt, selected, None, writer_opts)
        written.append((fmt, "-", count))
    else:
        out_dir = Path(args.out)
        for fmt in formats:
            path = out_dir / (name + WRITERS[fmt].extension)
            try:
                count = write_format(fmt, selected, path, writer_opts)
            except ValueError as exc:
                print("%s: %s" % (fmt, exc), file=sys.stderr)
                return 1
            written.append((fmt, str(path), count))

    # 汇总
    for report in reports:
        print("读取 %s：%s 布局，头 %d 字节，%d 块 → %d 条（跳过 %d）"
              % (report.path, report.layout, report.header_size,
                 report.blocks, report.entries, report.skipped))
    if reports and any(r.skipped for r in reports):
        print("  跳过原因：%s" % ", ".join(
            "%s=%d" % (k, v) for r in reports for k, v in r.reasons.items()))
    print(summarize(entries, "解析："))
    print(summarize(selected, "输出："))
    if args.stats:
        for entry in selected[:10]:
            print("  · %s\t%s" % (entry.text, entry.pinyin))
    for fmt, path, count in written:
        print("  %-10s %6d 条 → %s" % (fmt, count, path))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
