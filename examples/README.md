# examples

这里的文件都是**假数据**，由 `mspinyin_udl.testing` 生成，不含任何人的真实词库：

* `sample-ChsPinyinUDL.dat` —— 10 条示例词的假 `.dat`，可以拿来试跑：

  ```bash
  mspinyin-udl examples/sample-ChsPinyinUDL.dat -f all -o out
  ```

* `demo.dict.yaml` / `demo.tsv` / `demo.ms-phrase.txt` —— 上面这个假文件转换出来的结果，
  用来看输出长什么样（默认过滤掉「阿达哒哒哒」那条，所以是 9 条）。

真实的 `.dat` 请从自己的电脑导出，**不要提交到仓库**（`.gitignore` 已经排除了）。
