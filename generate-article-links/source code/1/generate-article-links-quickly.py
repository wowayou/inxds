import os
import sys
import json
import html
import gettext
import re
from bs4 import BeautifulSoup
from datetime import datetime

# 初始化国际化
_ = gettext.gettext

# 在文件顶部添加异常类定义
class TooManyFilesError(Exception):
    """Custom exception raised when the number of files exceeds the limit."""
    pass

class ArticleLinkGenerator:
    """文章链接生成器主类"""
    
    def __init__(self):
        self.config = self._load_config()
        self.templates = self._load_templates()
        
    def _load_config(self):
        """加载配置文件"""
        config_path = self._get_resource_path('config.json')
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(_("配置文件未找到，使用默认配置"))
            return {
                'max_files': {
                    1: 10,    # 根目录最新文章限制10篇
                    2: float('inf'),  # 侧边栏无限制
                    3: float('inf'),  # 相关文章无限制
                    4: float('inf'),  # 各系列index无限制
                    5: float('inf'),  # More Software and Computer Usage Tips无限制
                    6: 3,     # 首页的三个顶部文章
                    7: 3      # 各系列index的三个顶部文章
                },
                'template_files': {
                    '1': 'template_root.html',
                    '2': 'template_sidebar.html',
                    '3': 'template_related.html',
                    '4': 'template_series.html',
                    '5': 'template_more_tips.html',
                    '6': 'template_top_articles.html',
                    '7': 'template_series_top_articles.html'
                }
            }

    def _get_resource_path(self, filename):
        """获取资源文件路径"""
        if getattr(sys, 'frozen', False):
            base_dir = sys._MEIPASS if filename.endswith(('.html', '.json')) else os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))
        # 如有需要，可在此处对路径进行正斜杠替换，但通常仅生成的 HTML 需要统一分隔符
        return os.path.normpath(os.path.join(base_dir, filename))

    def _load_templates(self):
        """预加载所有模板"""
        templates = {}
        for t_type, t_file in self.config['template_files'].items():
            path = self._get_resource_path(os.path.join('templates', t_file))
            with open(path, 'r', encoding='utf-8') as f:
                templates[int(t_type)] = f.read()
        return templates

    def _normalize_path(self, path):
        """规范化路径处理，统一使用正斜杠"""
        # 替换所有反斜杠，然后用 os.path.normpath规范，再将系统分隔符替换为 /
        return os.path.normpath(path.replace('\\', '/')).replace(os.path.sep, '/')

    # def _check_unescaped_quotes(self, raw_content, url):
    #     """改进的引号检查方法，能检测嵌套引号"""
    #     # 改进正则表达式，更严格匹配description标签
    #     pattern = r'<meta\s+name=["\']description["\']\s+content=(["\'])(.*)\1'
    #     matches = re.finditer(pattern, raw_content, re.IGNORECASE | re.DOTALL)
        
    #     for match in matches:
    #         quote_type = match.group(1)
    #         content = match.group(2)
            
    #         # 检查未转义的双引号
    #         if quote_type == '"':
    #             unescaped = [m.start() for m in re.finditer(r'(?<!\\)"', content)]
    #             if unescaped:
    #                 print(f"关键警告: 文件 {url} 存在未转义双引号，位置: description, 可能是嵌套引号，请修改源文件后重新生成\n")
            
    #         # 检查未转义的单引号
    #         elif quote_type == "'":
    #             unescaped = [m.start() for m in re.finditer(r"(?<!\\)'", content)]
    #             if unescaped:
    #                 print(f"关键警告: 文件 {url} 存在未转义单引号，位置: description, 可能是嵌套引号，请修改源文件后重新生成\n")

    #     # 检查整个content属性是否完整闭合
    #     if not list(matches):
    #         print(f"警告: 文件 {url} 的description meta标签格式异常或未闭合")

    def _parse_article_metadata(self, soup, raw_content):
        """解析文章元数据"""
        try:
            title = soup.find('title').text
            description = soup.find('meta', {'name': 'description'}).get('content', '')
            url = soup.find('link', {'rel': 'canonical'}).get('href', '')
            
            # # 确保传入raw_content进行引号检查
            # if raw_content:
            #     self._check_unescaped_quotes(raw_content, url)
                
            return {
                'title': title,
                'description': description,
                'url': self._normalize_path(url.replace("https://www.shareus.com/", "")),
                'category': url.split('/')[3].upper() if url and len(url.split('/')) > 3 else "UNKNOWN",
                'date': self._convert_date(soup.find('p', class_='posted_date').text.strip()) 
                        if soup.find('p', class_='posted_date') else "",
                'img_src': self._process_image(soup.find('img', class_='feature_img'), url)
            }
        except AttributeError as e:
            print(_("HTML解析错误: {}").format(e))
            return None    

    def _process_image(self, img_tag, url):
        """处理图片路径"""
        if not img_tag:
            print(_("警告: 文件 {} 的首图可能为视频或无首图").format(url))
            img_src = "default-image.webp"
            default_path = self._get_resource_path(os.path.join('images', img_src))
            if not os.path.exists(default_path):
                print(_("警告: 默认图片 {} 不存在").format(default_path))
            return img_src
        
        # 先替换../和后缀，再使用 _normalize_path 确保使用正斜杠
        return self._normalize_path(img_tag['src'].replace("../", "").replace(".webp", "-m.webp"))

    def _convert_date(self, date_str):
        """日期格式转换"""
        date_str = date_str.strip()
        formats = ['%B %d, %Y', '%B %d %Y', '%B %d,%Y', '%b %d, %Y', '%b %d %Y']
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt).strftime('%Y-%m-%d')
            except ValueError:
                continue
        print(_("日期转换错误: '{}'").format(date_str))
        return "0000-00-00"

    def _adjust_paths_for_template(self, metadata, template_type):
        """根据模板类型调整路径"""
        if template_type in [2, 3, 4, 7]:
            # 对于模板类型，先加上前缀
            metadata['url'] = '../' + metadata['url']
            metadata['img_src'] = '../' + metadata['img_src']
            # 模板4和7只需要保留文件名
            if template_type in [4, 7]:
                metadata['url'] = metadata['url'].split('/')[-1]
            # 模板4调整图片后缀
            if template_type == 4:
                metadata['img_src'] = metadata['img_src'].replace("m.webp", "s.webp")
        # 最后统一规范化路径，确保所有分隔符均为 /
        metadata['url'] = self._normalize_path(metadata['url'])
        metadata['img_src'] = self._normalize_path(metadata['img_src'])
        return metadata

    def generate_html(self, content, template_type, item_number=None):
        """生成HTML代码"""
        soup = BeautifulSoup(content, 'html.parser')
        # 确保传递原始内容content以进行引号检查
        metadata = self._parse_article_metadata(soup, content)
        if not metadata:
            return ""
            
        metadata = self._adjust_paths_for_template(metadata, template_type)
        
        # 转义处理
        escaped_data = {
            'url': html.escape(metadata['url']),
            'category': html.escape(metadata['category']),
            'img_src': html.escape(metadata['img_src']),
            'title': html.escape(metadata['title']),
            'datetime': html.escape(metadata['date']),
            'date': html.escape(metadata['date']),
            'description': html.escape(metadata['description']),
            'item_number': item_number if template_type == 6 else '',
            'alt_title': html.escape(metadata['title']).replace('"', '&quot;').replace('&', '&amp;')
        }

        return self.templates.get(template_type, "").format(**escaped_data)

    def process_files(self, file_list_path, template_type):
        """处理文件列表"""
        paths = self._read_file_paths(file_list_path)
        max_files = self.config['max_files'].get(str(template_type))
        
        # 处理None值情况
        if max_files is None:
            max_files = float('inf')
        
        if len(paths) > max_files:
            raise TooManyFilesError(_("文件数量超过限制: {}").format(max_files))
            
        outputs = []
        for index, path in enumerate(paths, start=1):
            try:
                content = self._get_file_content(path)
                html_code = self.generate_html(content, template_type, index if template_type == 6 else None)
                if html_code:
                    outputs.append(html_code)
            except Exception as e:
                print(_("处理文件 {} 时出错: {}").format(path, e))

        if template_type == 1:
            outputs.reverse()
        return outputs

    def _read_file_paths(self, file_path):
        """读取文件路径列表"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return [self._normalize_path(path.strip()) for path in f 
                        if not (path.strip().startswith('#') or path.strip().startswith('//'))]
        except Exception as e:
            raise Exception(_("读取文件路径时发生错误: {}").format(e))

    def _get_file_content(self, path):
        """读取文件内容"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            raise FileNotFoundError(_("文件未找到: {}").format(path))
        except Exception as e:
            raise Exception(_("读取文件时发生错误: {}").format(e))

if __name__ == "__main__":
    # 设置语言环境
    try:
        lang = gettext.translation('messages', localedir='locales', languages=['zh_CN'])
        lang.install()
    except FileNotFoundError:
        gettext.install('messages')

    generator = ArticleLinkGenerator()
    
    try:
        script_dir = os.path.dirname(sys.executable if getattr(sys, 'frozen', False) 
                                   else os.path.abspath(__file__))
        file_list_path = os.path.join(script_dir, 'urls.txt')
        
        prompt = _(
            "请选择你要生成的网页链接类型:\n"
            "1. 根目录最新文章\n"
            "2. 侧边栏最新文章\n"
            "3. 相关文章\n"
            "4. 各系列index\n"
            "5. More Software and Computer Usage Tips\n"
            "6. 首页的三个顶部文章\n"
            "7. 各系列index的三个顶部文章\n"
            "选择（1/2/3/4/5/6/7，默认3）: "
        )
        
        choice = input(prompt)
        template_type = int(choice) if choice else 3
        
        if template_type not in range(1, 8):
            raise ValueError(_("无效的选择"))
            
        for html_code in generator.process_files(file_list_path, template_type):
            print(html_code)
            
        input(_("按回车键退出..."))
        
    except Exception as e:
        print(_("发生错误: {}").format(e))
