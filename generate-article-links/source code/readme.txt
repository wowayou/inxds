功能：
生成链接，包括
1. 根目录index.html的最新文章
2. 侧边栏最新文章
3. 文章的相关文章
4. 各系列index.html的文章链接
5. 根目录index.html中 More Software and Computer Usage Tips 部分的链接
6. 根目录index.html 的三个顶部文章
7. 各系列index.html 顶部三篇文章

Preparation Steps:
- Install Python:
Visit the official Python website at python.org and download the latest stable version of Python for Windows. 
During installation, make sure to check the box that says "Add Python to PATH" or similar. This allows you to run Python from any command prompt.

- Install Required Libraries:
Open the command prompt (cmd or PowerShell) or use a terminal in your code editor like VSCode:
Install required packages:
pip install beautifulsoup4 tkinter(如果使用2的话，需要安装这个）

=====================
1
generate-article-links-quickly.py (推荐 1) 之后对2不会再做维护。
使用步骤：
1. 将需要生成链接的html文件的本地文件路径 写入urls.txt
2. 运行脚本
- 打开命令提示符
- 切换到脚本所在目录 (cd 命令)
- 使用 python generate-article-links-quickly.py 命令运行脚本
根据提示生成所需链接

=====================================
2
generate-article-links-quickly-interactive.py（调出文件选择框，优点是可以交互性地选择文件；缺点是：不支持跨目录进行多选）

使用方法
1. 打开命令提示符
2. 切换到脚本所在目录 cd 命令
3. 使用 python xx.py 命令运行脚本
4. 检查 生成的 html_generator.log 文件，查看是否有什么问题。

Setup Files:
templates.py 保存了各部分链接的模板
config.json 配置文件，包括模板文件位置，默认打开路径(需要根据自己的路径改一下)，最大文件数量限制，日志文件位置等