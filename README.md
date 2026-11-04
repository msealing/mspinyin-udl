# mspinyin-udl

把**微软拼音导出的私有词库**（`ChsPinyinUDL.dat` / `ChsPinyinIH.dat`）转换成
Rime、通用文本、微软自定义短语等多种格式。

[![CI](https://github.com/msealing/mspinyin-udl/actions/workflows/ci.yml/badge.svg)](https://github.com/msealing/mspinyin-udl/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)](pyproject.toml)

> 零依赖、纯 Python、全部本地运行。不上传、不联网、不需要账号。

---

## 为什么需要它

微软拼音把「自学习」的词存在 `%APPDATA%\Microsoft\InputMethod\Chs\ChsPinyinUDL.dat` 里，
这是个**没公开的二进制格式**：

* 网上能找到的工具基本只把里面的**汉字**抠出来（取证用途），**没有拼音**；
* 通用词库转换工具（深蓝词库转换等）**不认识**这个后缀；
* 微软自己只能在「导入词库」里吃回自己的 `.dat`，不吃别的格式。

结果就是：想把用了多年的微软拼音词库搬到 Rime / fcitx5 / 其他输入法，基本无路可走。

本项目把这个格式拆开，并且**把拼音精确还原**（不是猜的）：

* 每条记录里，每个汉字后面都跟着一个 `uint16`，是内置 413 项音节表的下标；
* 所以多音字也不用猜——`重庆` → `chong qing`、`银行` → `yin hang`、`角色` → `jue se`；
* 再按你需要的格式输出。

格式细节写在 [docs/format.md](docs/format.md)。

## 支持哪些输入

| 文件 | 内容 | 能还原拼音 |
| --- | --- | --- |
| `ChsPinyinUDL.dat` | 自学习 / 用户词库 | ✅ |
| `ChsPinyinUDL_Beta.dat`、`*_RoamDown.dat` | 同上（Beta / 漫游） | ✅ |
| `ChsPinyinIH.dat` | 输入历史 | ❌ 只有词 |

文件位置：

```
%APPDATA%\Microsoft\InputMethod\Chs\
```

也可以在「设置 → 时间和语言 → 语言 → 中文(简体) → 选项 → 微软拼音 → 词库和自学习」
里点「导出词库」。

## 安装

```bash
pipx install git+https://github.com/msealing/mspinyin-udl
# 或者
pip install git+https://github.com/msealing/mspinyin-udl
```

也可以把仓库 clone 下来直接用（不用安装、不联网）：

```bash
git clone https://github.com/msealing/mspinyin-udl
cd mspinyin-udl
python run.py ChsPinyinUDL.dat -f all -o out
```

`run.py` 等价于安装后的 `mspinyin-udl` 命令，Windows 上的 `convert.bat` 用的就是它。

> 只有 Python 3.9+ 标准库，没有任何第三方依赖。

## 快速开始

### Windows：拖拽

把 `.dat` 文件拖到仓库里的 **`convert.bat`** 上，会在 `.dat` 旁边生成 `out\` 目录，
里面是全部格式。

### 命令行

```bash
# 默认输出 Rime 词典 + 通用 TSV
mspinyin-udl ChsPinyinUDL.dat

# 输出全部格式
mspinyin-udl ChsPinyinUDL.dat -f all -o out

# 合并「词库」和「输入历史」，去重后输出
mspinyin-udl ChsPinyinUDL.dat ChsPinyinIH.dat -f tsv --name merged

# 保留测试性词条（默认会过滤）
mspinyin-udl ChsPinyinUDL.dat -f rime --noisy

# 直接输出到屏幕
mspinyin-udl ChsPinyinUDL.dat -f rime --stdout
```

输出示例：

```
读取 ChsPinyinUDL.dat：udl 布局，头 9216 字节，16401 块 → 16395 条（跳过 5）
解析：共 16395 条（2字:2815 3字:6862 4字:4427 …）
输出：共 15332 条（2字:2759 3字:6705 4字:4283 …）
  rime          15332 条 → out/ChsPinyinUDL.dict.yaml
  tsv           15332 条 → out/ChsPinyinUDL.tsv
  …
```

## 输出格式

| `-f` | 扩展名 | 内容 | 给谁用 |
| --- | --- | --- | --- |
| `rime` | `.dict.yaml` | `text / code / weight` 三列 | Rime（小狼毫、鼠须管、同文、fcitx5-rime…） |
| `tsv` | `.tsv` | `词⇥拼音⇥词频` | 支持「词 + 拼音 + 词频」文本词库的工具 |
| `txt` | `.txt` | `词⇥拼音` | 各种「文本词库 / 自定义短语」导入 |
| `csv` | `.csv` | `text, pinyin, weight` | Excel / 脚本 |
| `json` | `.json` | 数组，含 `syllables` 拆分 | 自己写程序接着处理 |
| `words` | `.words.txt` | 每行一个词 | 会自己推读音的工具 |
| `ms-phrase` | `.ms-phrase.txt` | `拼音码,位置,短语` | 微软拼音「用户自定义短语」导入 |
| `template` | `.txt` | 由 `--template` 决定 | 其它任何文本格式 |
| `all` | — | 上面除 `template` 外全部 | 一次全出 |

### `ms-phrase`：把词库导回微软拼音

微软拼音的「用户自定义短语」支持导入文本，格式为 `拼音码,位置,短语`：

```
zuozhanjihua,1,作战计划
yinhang,1,银行
```

用 `--ms-position 2` 可以指定固定候选位置（1–9）。

> 这个格式是社区里流传的导入格式，不同 Windows / 输入法版本可能略有差异。
> 建议先拿几条试导入，确认能出现在候选里再整批导入。

### `template`：接任何输入法

有些输入法只要文本，格式五花八门。用模板自己拼：

```bash
mspinyin-udl ChsPinyinUDL.dat -f template \
  --template "{text},{pinyin},{weight}" -o out
```

可用占位符：`{index}` `{text}` / `{word}` `{pinyin}` `{pinyin_joined}` `{weight}`，
反斜杠 `\t`、`\n` 会被转义。

## 常用参数

| 参数 | 说明 |
| --- | --- |
| `-f, --format` | 输出格式，逗号分隔或 `all`；`mspinyin-udl --list-formats` 看全表 |
| `-o, --out` | 输出目录（默认 `out`） |
| `-n, --name` | 输出文件名（默认取源文件名） |
| `--sep` | 拼音音节分隔符（默认空格） |
| `--joined` | 拼音连写：`nihao` 而不是 `ni hao` |
| `--weight` | 词频列取值（默认 100；`.dat` 里没有词频，只能用常数） |
| `--noisy` / `--all` | 保留测试性词条 |
| `--min-chars` / `--max-chars` | 按词长过滤 |
| `--keep-duplicates` / `--dedupe-pinyin` | 去重策略 |
| `--layout` | `auto` / `udl` / `ih`，强制文件类型 |
| `--header` | 手动指定文件头长度（布局变了时用） |
| `--stdout` | 输出到标准输出（只能配一种格式） |
| `--stats` | 打印解析/过滤统计和样例 |

`mspinyin-udl --help` 看完整说明。

## 关于「噪声词条」

微软的「自学习」会把你打过的候选都记下来。如果你曾在输入法里敲过单个字母试输入，
就会攒下一大批 `啊啊啊啊`、`阿达哒哒哒`、`水水水水水` 这样的词条（实测约占 6%）。

默认会过滤掉：

* 含 `啊 哒 顶 哇 饿` 这类测试常用字的；
* 同一字符连续出现 ≥ 3 次的。

用 `--noisy` 保留全部；`--noise-chars` / `--max-repeat` 可以自定义规则。

## 工作原理（简述）

见 [docs/format.md](docs/format.md)。三句话：

1. 文件 = 文件头（UDL 9216 / IH 5120 字节）+ 定长 60 字节记录数组；
2. UDL 记录 = 4 字节哈希 + 3 个模糊首字母 + 字数 + `0x5A` + UTF-16LE 汉字 + 每字一个 `uint16`；
3. 这个 `uint16` 是 413 项普通话音节表的下标，查表即得拼音。

## 已知限制

* **没有词频**：`.dat` 是按拼音排序的，不存使用次数，所以 `weight` 是常数。
* **只有「词」**：用户置顶的候选、自定义短语、屏蔽词不在这个文件里。
* **格式未公开**：不同 Windows 版本布局可能变化。遇到解析失败，用 `--header` 试，
  或者开 issue 贴一段 hexdump（**别贴完整词库，里面有你的隐私**）。
* **IH 没有拼音**：只有词，需要读音的格式会自动跳过或留空。
* **不写 `.dat`**：本工具只做「读出来」，不做「写回去」。

## 隐私

所有转换都在本地完成，不联网。仓库里**不包含**任何人的真实词库；
测试用的是 `mspinyin_udl.testing` 生成的假数据。

`.gitignore` 已经排除了 `ChsPinyin*.dat`，避免你手滑提交自己的词库。

## 开发

```bash
python -m pip install -e .
python -m unittest discover -s tests -v      # 50 个测试
python tools/make_sample_dat.py sample.dat    # 生成假 .dat 试玩
```

想加一种输出格式：在 `src/mspinyin_udl/writers.py` 写一个
`writer(entries, path, options) -> int`，再注册到 `WRITERS` 里即可。

### 发布与版本

仓库托管在 <https://github.com/msealing/mspinyin-udl>。发新版本时：

```bash
# 1. 改 pyproject.toml / CHANGELOG.md 里的版本号并提交
git tag v0.1.0
git push --tags
```

CI（`.github/workflows/ci.yml`）会在 push 后自动在 Linux / macOS / Windows 上跑测试。

## English

A dependency-free converter for Microsoft Pinyin's proprietary user dictionaries
(`ChsPinyinUDL.dat` / `ChsPinyinIH.dat`). Syllables are recovered exactly from the
embedded syllable-table indices, so polyphones are preserved. Output formats:
Rime `.dict.yaml`, TSV/TXT/CSV/JSON, plain word lists, Microsoft Pinyin custom
phrases, and a template mode for anything else.

```bash
pipx install git+https://github.com/msealing/mspinyin-udl
mspinyin-udl ChsPinyinUDL.dat -f all -o out
```

## License

[MIT](LICENSE)。这个项目与微软无关；`.dat` 格式是逆向所得，仅供参考。
