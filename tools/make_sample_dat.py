# -*- coding: utf-8 -*-
"""生成**假的** ChsPinyinUDL.dat / ChsPinyinIH.dat，供测试和演示用。

不含任何人的真实词库，只按格式写几条示例词。

    python tools/make_sample_dat.py sample_udl.dat
    python tools/make_sample_dat.py sample_ih.dat --layout ih
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mspinyin_udl.testing import build_ih, build_udl  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description="生成测试用的假 .dat")
    ap.add_argument("out", help="输出文件")
    ap.add_argument("--layout", choices=["udl", "ih"], default="udl")
    args = ap.parse_args()
    data = build_udl() if args.layout == "udl" else build_ih()
    Path(args.out).write_bytes(data)
    print("已写出 %s（%d 字节，%s）" % (args.out, len(data), args.layout))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
