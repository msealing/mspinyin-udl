#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""不安装也能直接跑：

    python run.py ChsPinyinUDL.dat -f all -o out

（等价于安装后的 ``mspinyin-udl`` 命令。）
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent / "src"))

from mspinyin_udl.cli import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
