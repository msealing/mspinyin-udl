# Changelog

## 0.1.0

首个版本。

* 解析 `ChsPinyinUDL.dat`（词库 / 自学习，带音节序号，可还原拼音）
* 解析 `ChsPinyinIH.dat`（输入历史，只有词）
* 多文件合并、按词去重
* 噪声过滤（默认过滤「啊啊啊」「阿达哒哒哒」这类敲单字母试出来的词）
* 输出格式：`rime`、`tsv`、`txt`、`csv`、`json`、`words`、`ms-phrase`、`template`
* 命令行：`--format all`、`--stdout`、`--joined`、`--stats`、`--header` 等
* 50 个单元测试，内置 `run.py`（免安装入口）与 `convert.bat`（拖拽即转）
* CI 覆盖 Linux / macOS / Windows 与 Python 3.9–3.13
