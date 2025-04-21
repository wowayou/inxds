#### 基本功能：
批量检查指定文件夹中所有html文件中的拼写错误

#### 功能：

支持自定义跳过的单词、错误、标签。在 `config.json` 中配置。
支持断点续传（中断之后从上次中断的地方继续检查）；过程中会生成一份 `processed_files.txt` 文件。

#### 使用

- 打开命令提示符，切换到脚本所在路径。（或者在脚本所在路径打开命令提示符）

- 执行 `python language-tool-lib-spell-checker.py ` 运行脚本；

会生成 `processed_files.txt` 和 `spell_report.json` 文件(json格式方便处理)。

- 接着，运行 `python convert-json-to-csv(alternative).py` ；生成 `correction_suggestions_*_*.csv` 文件(更加方便查看)
- 打开 `report.html` 网页，选择刚刚生成的 csv 文件，开始进行拼写修改；（todo 持久化保存处理进度）

其实report.html 可视化，可以直接使用 json （我感觉）；先实现功能再说。

优先级：

```text
title/meta/h1 中的错误 → 优先处理；
正文中首段/结尾段错误 → 次优先；
页脚、隐藏标签内错误 → 最后处理；
```

现在的问题，

1. processed_files 是最后生成的，如果脚本执行过程中出问题，可能无法保存进度

优化？



