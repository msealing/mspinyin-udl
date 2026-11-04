# -*- coding: utf-8 -*-
import contextlib
import io
import os
import subprocess
import sys
import unittest
from pathlib import Path

from mspinyin_udl.cli import main
from mspinyin_udl.testing import build_ih, build_udl
from support import temp_dir


def run(argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = main(argv)
    return code, out.getvalue(), err.getvalue()


class TestCli(unittest.TestCase):
    def setUp(self):
        self._ctx = temp_dir()
        self.dir = self._ctx.__enter__()
        self.dat = self.dir / "ChsPinyinUDL.dat"
        self.dat.write_bytes(build_udl())

    def tearDown(self):
        self._ctx.__exit__(None, None, None)

    def test_default_formats(self):
        out_dir = self.dir / "out"
        code, stdout, _ = run([str(self.dat), "-o", str(out_dir)])
        self.assertEqual(code, 0)
        self.assertTrue((out_dir / "ChsPinyinUDL.dict.yaml").is_file())
        self.assertTrue((out_dir / "ChsPinyinUDL.tsv").is_file())
        self.assertIn("解析：", stdout)

    def test_all_formats(self):
        out_dir = self.dir / "out"
        code, _, _ = run([str(self.dat), "-f", "all", "-o", str(out_dir), "--name", "demo"])
        self.assertEqual(code, 0)
        for name in ("demo.dict.yaml", "demo.tsv", "demo.txt", "demo.csv",
                     "demo.json", "demo.words.txt", "demo.ms-phrase.txt"):
            self.assertTrue((out_dir / name).is_file(), name)

    def test_noise_filtered_by_default(self):
        out_dir = self.dir / "out"
        run([str(self.dat), "-f", "tsv", "-o", str(out_dir), "--name", "demo"])
        rows = [l for l in (out_dir / "demo.tsv").read_text(encoding="utf-8").splitlines()
                if l and not l.startswith("#")]
        self.assertEqual(len(rows), 9)          # 10 条里去掉「阿达哒哒哒」

    def test_keep_noisy(self):
        out_dir = self.dir / "out"
        run([str(self.dat), "-f", "tsv", "-o", str(out_dir), "--name", "demo", "--noisy"])
        rows = [l for l in (out_dir / "demo.tsv").read_text(encoding="utf-8").splitlines()
                if l and not l.startswith("#")]
        self.assertEqual(len(rows), 10)

    def test_stdout(self):
        code, stdout, _ = run([str(self.dat), "-f", "rime", "--stdout"])
        self.assertEqual(code, 0)
        self.assertIn("中国\tzhong guo", stdout)

    def test_stdout_requires_single_format(self):
        code, _, err = run([str(self.dat), "-f", "rime,tsv", "--stdout"])
        self.assertEqual(code, 1)
        self.assertIn("单一格式", err)

    def test_history_file(self):
        ih = self.dir / "ChsPinyinIH.dat"
        ih.write_bytes(build_ih())
        out_dir = self.dir / "out"
        code, _, _ = run([str(ih), "-f", "words", "-o", str(out_dir), "--name", "hist"])
        self.assertEqual(code, 0)
        lines = (out_dir / "hist.words.txt").read_text(encoding="utf-8").splitlines()
        self.assertEqual(lines[0], "中国")

    def test_missing_file(self):
        code, _, err = run([str(self.dir / "nope.dat")])
        self.assertEqual(code, 1)
        self.assertIn("找不到文件", err)

    def test_no_inputs(self):
        code, _, _ = run([])
        self.assertEqual(code, 2)

    def test_unknown_format(self):
        code, _, err = run([str(self.dat), "-f", "nope"])
        self.assertEqual(code, 1)
        self.assertIn("未知格式", err)

    def test_list_formats(self):
        code, stdout, _ = run(["--list-formats"])
        self.assertEqual(code, 0)
        self.assertIn("rime", stdout)
        self.assertIn("ms-phrase", stdout)

    def test_stats_and_limit(self):
        code, stdout, _ = run([str(self.dat), "-f", "tsv", "-o", str(self.dir / "o"), "--stats"])
        self.assertEqual(code, 0)
        self.assertIn("·", stdout)

    def test_run_py_works_without_install(self):
        """run.py 是不安装也能跑的入口，Windows 的 convert.bat 依赖它。"""
        root = Path(__file__).resolve().parents[1]
        proc = subprocess.run(
            [sys.executable, str(root / "run.py"), "--version"],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("mspinyin-udl", proc.stdout)

    def test_run_py_converts(self):
        root = Path(__file__).resolve().parents[1]
        out_dir = self.dir / "out-runpy"
        proc = subprocess.run(
            [sys.executable, str(root / "run.py"), str(self.dat),
             "-f", "tsv", "-o", str(out_dir), "--name", "demo"],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertTrue((out_dir / "demo.tsv").is_file())


if __name__ == "__main__":
    unittest.main()
