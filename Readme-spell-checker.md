#### 基本功能：
批量检查指定文件夹中所有html文件中的拼写错误

#### 功能：

支持自定义跳过的单词、错误、标签。在 `config.json` 中配置。
支持断点续传（中断之后从上次中断的地方继续检查）；过程中会生成一份 `processed_files.txt` 文件。

#### 使用

- 打开命令提示符，切换到脚本所在路径。（或者在脚本所在路径打开命令提示符）

- 执行 `python language-tool-lib-spell-checker.py ` 运行脚本；

会生成 `processed_files.txt` 和 `spell_report.json` 文件(json格式方便处理)。

- 接着，运行 `python spell-fix-suggestion.py` ；生成 `correction_suggestions.csv` 文件(更加方便查看)
- 打开 `report.html` 网页，选择刚刚生成的 csv 文件，开始进行拼写修改；（todo 持久化保存处理进度）[可视化]
- 

