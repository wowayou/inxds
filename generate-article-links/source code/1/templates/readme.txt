优势
模块化
模板与逻辑分离，修改HTML结构只需编辑模板文件，无需改动Python代码。
可扩展性
添加新模板只需创建新文件并更新 template_files 字典。脚本也需要简单微调

template_root.html 根index最新文章
template_sidebar.html 侧边栏最新文章
template_top_articles.html 根index顶部三个文章
template_related.html 普通文章的相关文章部分
template_series.html 添加到系列index 页面的文章链接
template_more_tips.html 根index的 More Software and Computer Usage Tips
template_series_top_articles.html 各系列index顶部文章(software/软件名称/index.html 的不适用，）需要手动编辑图片地址和链接地址(三处，两处a href，一处 img src))