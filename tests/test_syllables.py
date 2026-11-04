# -*- coding: utf-8 -*-
import unittest

from mspinyin_udl.syllables import SYLLABLE_COUNT, SYLLABLE_TABLE, syllable


class TestSyllableTable(unittest.TestCase):
    def test_size(self):
        self.assertEqual(SYLLABLE_COUNT, 413)
        self.assertEqual(len(SYLLABLE_TABLE), 413)

    def test_sorted_and_unique(self):
        self.assertEqual(list(SYLLABLE_TABLE), sorted(SYLLABLE_TABLE))
        self.assertEqual(len(set(SYLLABLE_TABLE)), 413)

    def test_spot_checks(self):
        # 这些下标是在真实文件里核对过的
        self.assertEqual(SYLLABLE_TABLE[0], "a")
        self.assertEqual(SYLLABLE_TABLE[56], "da")        # 大打达哒答 → da
        self.assertEqual(SYLLABLE_TABLE[395], "zhong")    # 终 → zhong
        self.assertEqual(SYLLABLE_TABLE[412], "zuo")      # 作 → zuo
        self.assertEqual(SYLLABLE_TABLE[123], "hou")      # 后 → hou
        self.assertEqual(SYLLABLE_TABLE[354], "xing")     # 醒 → xing

    def test_lookup_error(self):
        with self.assertRaises(LookupError):
            syllable(413)
        with self.assertRaises(LookupError):
            syllable(-1)

    def test_every_syllable_is_ascii(self):
        for s in SYLLABLE_TABLE:
            self.assertRegex(s, r"^[a-z]+$")


if __name__ == "__main__":
    unittest.main()
