# -*- coding: utf-8 -*-
import unittest

from mspinyin_udl.datfile import Entry
from mspinyin_udl.filters import (
    FilterOptions,
    apply,
    is_noisy,
    max_char_run,
    summarize,
)


def entries(*texts):
    out = []
    for text in texts:
        out.append(Entry(text=text, syllable_ids=tuple([0] * len(text))))
    return out


class TestNoise(unittest.TestCase):
    def test_noise_chars(self):
        self.assertTrue(is_noisy("啊啊啊"))
        self.assertTrue(is_noisy("阿达哒哒哒"))
        self.assertTrue(is_noisy("我顶顶顶"))

    def test_repeat_rule(self):
        self.assertTrue(is_noisy("水水水水"))
        self.assertFalse(is_noisy("打打杀杀"))
        self.assertEqual(max_char_run("水水水水"), 4)

    def test_clean_words(self):
        self.assertFalse(is_noisy("作战计划"))
        self.assertFalse(is_noisy("进行数据分析"))


class TestApply(unittest.TestCase):
    def test_default_filters_noise(self):
        result = apply(entries("作战计划", "啊啊啊", "阿达哒哒哒", "进行数据分析"))
        self.assertEqual([e.text for e in result], ["作战计划", "进行数据分析"])

    def test_keep_noisy(self):
        result = apply(entries("作战计划", "啊啊啊"), FilterOptions(keep_noisy=True))
        self.assertEqual(len(result), 2)

    def test_dedupe(self):
        result = apply(entries("你好", "你好", "中国"))
        self.assertEqual([e.text for e in result], ["你好", "中国"])

    def test_keep_duplicates(self):
        result = apply(entries("你好", "你好"), FilterOptions(dedupe=False))
        self.assertEqual(len(result), 2)

    def test_min_max_chars(self):
        result = apply(entries("好", "你好", "进行数据分析"),
                       FilterOptions(min_chars=2))
        self.assertEqual([e.text for e in result], ["你好", "进行数据分析"])
        result = apply(entries("好", "你好", "进行数据分析"),
                       FilterOptions(max_chars=2))
        self.assertEqual([e.text for e in result], ["好", "你好"])

    def test_summarize(self):
        text = summarize(entries("你好", "中国", "进行数据分析"), "输出：")
        self.assertIn("共 3 条", text)
        self.assertIn("2字:2", text)


if __name__ == "__main__":
    unittest.main()
