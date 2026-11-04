# -*- coding: utf-8 -*-
import unittest
from pathlib import Path

from mspinyin_udl.datfile import Entry, read_dat, read_many
from mspinyin_udl.testing import build_ih, build_udl
from support import temp_dir


class TestUdl(unittest.TestCase):
    def setUp(self):
        self._ctx = temp_dir()
        self.tmp = self._ctx.__enter__()
        self.path = self.tmp / "ChsPinyinUDL.dat"
        self.path.write_bytes(build_udl())

    def tearDown(self):
        self._ctx.__exit__(None, None, None)

    def test_parse_all_entries(self):
        entries, report = read_dat(self.path)
        self.assertEqual(report.layout, "udl")
        self.assertEqual(report.header_size, 9216)
        self.assertEqual(report.entries, 10)
        self.assertEqual(report.skipped, 0)
        self.assertEqual(entries[0].text, "中国")
        self.assertEqual(entries[0].pinyin, "zhong guo")

    def test_polyphone_readings(self):
        entries, _ = read_dat(self.path)
        by_text = {e.text: e.pinyin for e in entries}
        self.assertEqual(by_text["重庆"], "chong qing")
        self.assertEqual(by_text["银行"], "yin hang")
        self.assertEqual(by_text["角色"], "jue se")
        self.assertEqual(by_text["处理"], "chu li")
        self.assertEqual(by_text["音乐"], "yin yue")
        self.assertEqual(by_text["作战计划"], "zuo zhan ji hua")

    def test_syllables_and_joined(self):
        entries, _ = read_dat(self.path)
        entry = next(e for e in entries if e.text == "进行数据分析")
        self.assertEqual(len(entry.syllables), 6)
        self.assertEqual(entry.pinyin_joined, "jinxingshujufenxi")
        self.assertTrue(entry.has_pinyin)

    def test_corrupted_block_is_skipped(self):
        data = bytearray(build_udl())
        first = 9216 + 60            # 第一条记录
        data[first + 11] = 0x00      # 破坏固定标记
        self.path.write_bytes(bytes(data))
        entries, report = read_dat(self.path)
        self.assertEqual(report.skipped, 1)
        self.assertEqual(report.entries, 9)
        self.assertNotIn("中国", [e.text for e in entries])

    def test_too_small_file(self):
        bad = self.tmp / "small.dat"
        bad.write_bytes(b"\x00" * 100)
        with self.assertRaises(ValueError):
            read_dat(bad)

    def test_explicit_header(self):
        entries, report = read_dat(self.path, layout="udl", header_size=9216)
        self.assertEqual(report.header_size, 9216)
        self.assertEqual(len(entries), 10)


class TestIH(unittest.TestCase):
    def setUp(self):
        self._ctx = temp_dir()
        self.tmp = self._ctx.__enter__()
        self.path = self.tmp / "ChsPinyinIH.dat"
        self.path.write_bytes(build_ih())

    def tearDown(self):
        self._ctx.__exit__(None, None, None)

    def test_parse_history(self):
        entries, report = read_dat(self.path)
        self.assertEqual(report.layout, "ih")
        self.assertEqual(report.header_size, 5120)
        self.assertEqual(report.entries, 10)
        self.assertEqual(entries[0].text, "中国")
        self.assertFalse(entries[0].has_pinyin)
        self.assertEqual(entries[0].pinyin, "")

    def test_merged_reads(self):
        udl = self.tmp / "ChsPinyinUDL.dat"
        udl.write_bytes(build_udl())
        merged, reports = read_many([udl, self.path])
        self.assertEqual(len(reports), 2)
        # 同一批词按「词 + 拼音」去重，UDL 那 10 条保留，IH 的 10 条里
        # 「阿达哒哒哒」等也因拼音不同而保留 → 共 20 条
        self.assertEqual(len(merged), 20)
        self.assertTrue(any(e.has_pinyin for e in merged))
        self.assertTrue(any(not e.has_pinyin for e in merged))


class TestEntry(unittest.TestCase):
    def test_properties(self):
        entry = Entry(text="你好", syllable_ids=(219, 113))
        self.assertEqual(entry.pinyin, "ni ha")
        self.assertEqual(entry.pinyin_joined, "niha")


if __name__ == "__main__":
    unittest.main()
