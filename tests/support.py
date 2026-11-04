# -*- coding: utf-8 -*-
"""测试辅助：一个不依赖 tempfile 的临时目录（某些受限环境里 mkdtemp 建出来的
目录会带上拒绝写入的 ACL，导致测试假失败）。"""
from __future__ import annotations

import contextlib
import shutil
import uuid
from pathlib import Path

BUILD_DIR = Path(__file__).resolve().parents[1] / "build"


@contextlib.contextmanager
def temp_dir():
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    path = BUILD_DIR / ("test-" + uuid.uuid4().hex[:12])
    path.mkdir(parents=True, exist_ok=False)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)
