# -*- coding: utf-8 -*-
import csv
import json
import unittest
from pathlib import Path

from mspinyin_udl.datfile import read_dat
from mspinyin_udl.testing import build_udl
from support import temp_dir
from mspinyin_udl.writers import (
    WRITERS,
    WriterOptions,
    resolve_formats,
    write_format,
)


class TestWriters(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._ctx = temp_dir()
        cls.tmp = cls._ctx.__enter__()
        dat = cls.tmp / "ChsPinyinUDL.dat"
        dat.write_bytes(build_udl())
        cls.entries, _ = read_dat(dat)
        cls.opts = WriterOptions(name="demo", weight=100)

    @classmethod
    def tearDownClass(cls):
        cls._ctx.__exit__(None, None, None)

    def path(self, name):
        return self.tmp / name

    def test_rime(self):
        out = self.path("demo.dict.yaml")
        count = write_format("rime", self.entries, out, self.opts)
        self.assertEqual(count, 10)
        lines = out.read_text(encoding="utf-8").splitlines()
        self.assertIn("name: demo", lines)
        self.assertIn("columns:", lines)
        self.assertIn("中国\tzhong guo\t100", lines)

    def test_tsv(self):
        out = self.path("demo.tsv")
        write_format("tsv", self.entries, out, self.opts)
        lines = out.read_text(encoding="utf-8").splitlines()
        self.assertTrue(lines[0].startswith("#"))
        self.assertEqual(lines[1].split("\t"), ["中国", "zhong guo", "100"])

    def test_txt(self):
        out = self.path("demo.txt")
        write_format("txt", self.entries, out, self.opts)
        self.assertIn("你好\tni hao", out.read_text(encoding="utf-8"))

    def test_csv(self):
        out = self.path("demo.csv")
        write_format("csv", self.entries, out, self.opts)
        with open(out, encoding="utf-8", newline="") as fh:
            rows = list(csv.reader(fh))
        self.assertEqual(rows[0], ["text", "pinyin", "weight"])
        self.assertEqual(rows[1], ["中国", "zhong guo", "100"])

    def test_json(self):
        out = self.path("demo.json")
        write_format("json", self.entries, out, self.opts)
        data = json.loads(out.read_text(encoding="utf-8"))
        self.assertEqual(len(data), 10)
        self.assertEqual(data[0]["text"], "中国")
        self.assertEqual(data[0]["syllables"], ["zhong", "guo"])

    def test_words(self):
        out = self.path("demo.words.txt")
        write_format("words", self.entries, out, self.opts)
        lines = out.read_text(encoding="utf-8").splitlines()
        self.assertEqual(lines[0], "中国")
        self.assertEqual(len(lines), 10)

    def test_ms_phrase(self):
        out = self.path("demo.ms-phrase.txt")
        write_format("ms-phrase", self.entries, out, WriterOptions(name="demo", ms_position=2))
        lines = out.read_text(encoding="utf-8").splitlines()
        self.assertEqual(lines[0], "zhongguo,2,中国")

    def test_template(self):
        out = self.path("demo.custom.txt")
        opts = WriterOptions(name="demo", template="{index}:{text}|{pinyin_joined}|{weight}")
        write_format("template", self.entries, out, opts)
        lines = out.read_text(encoding="utf-8").splitlines()
        self.assertEqual(lines[0], "1:中国|zhongguo|100")

    def test_template_requires_template(self):
        with self.assertRaises(ValueError):
            write_format("template", self.entries, self.path("x.txt"), WriterOptions())

    def test_joined_pinyin(self):
        out = self.path("joined.tsv")
        write_format("tsv", self.entries, out, WriterOptions(joined=True))
        self.assertIn("中国\tzhongguo\t100", out.read_text(encoding="utf-8"))

    def test_ms_phrase_skips_entries_without_pinyin(self):
        from mspinyin_udl.datfile import Entry
        out = self.path("nopinyin.ms-phrase.txt")
        entries = [Entry(text="中国", syllable_ids=(395, 112)), Entry(text="没有拼音")]
        count = write_format("ms-phrase", entries, out, WriterOptions())
        self.assertEqual(count, 1)

    def test_format_registry(self):
        self.assertIn("rime", WRITERS)
        self.assertIn("ms-phrase", WRITERS)
        self.assertEqual(len(WRITERS), 8)
        for fmt in WRITERS.values():
            self.assertTrue(fmt.extension.startswith("."))

    def test_resolve_formats(self):
        self.assertEqual(resolve_formats("rime"), ["rime"])
        self.assertEqual(resolve_formats("yaml"), ["rime"])
        self.assertEqual(resolve_formats("rime, tsv"), ["rime", "tsv"])
        # template 必须配 --template，所以不在 all 里
        self.assertEqual(set(resolve_formats("all")), set(WRITERS) - {"template"})
        with self.assertRaises(ValueError):
            resolve_formats("nope")


if __name__ == "__main__":
    unittest.main()
