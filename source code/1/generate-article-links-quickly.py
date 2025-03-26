import os
import sys
import json
from bs4 import BeautifulSoup
from datetime import datetime

class TooManyFilesError(Exception):
    """Custom exception raised when the number of files exceeds the limit."""
    pass

def read_file_paths(file_path):
    """读取文件路径列表，跳过注释行"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return [path.strip() for path in file.readlines() if not (path.strip().startswith('#') or path.strip().startswith('//'))]
    except Exception as e:
        raise Exception(f"读取文件路径时发生错误: {e}")

def get_file_content(path):
    """读取文件内容"""
    try:
        with open(path, 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError as e:
        raise FileNotFoundError(f"文件未找到: {path}")
    except Exception as e:
        raise Exception(f"读取文件时发生错误: {e}")

def convert_date(date_str):
    """将日期从 'MMMM dd, yyyy' 转换为 'yyyy-mm-dd'"""
    date_str = date_str.strip()
    formats = ['%B %d, %Y', '%B %d %Y', '%B %d,%Y', '%b %d, %Y', '%b %d %Y']
    for fmt in formats:
        try:
            date_obj = datetime.strptime(date_str, fmt)
            return date_obj.strftime('%Y-%m-%d')
        except ValueError:
            continue
    print(f"日期转换错误: '{date_str}' - 使用默认日期格式 'yyyy-mm-dd'")
    return "0000-00-00"

def load_template_files():
    """加载模板文件映射"""
    # 获取脚本或可执行文件所在的目录
    if getattr(sys, 'frozen', False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(base_dir, 'config.json')
    try:
        with open(config_path, 'r', encoding='utf-8') as config_file:
            config_data = json.load(config_file)
            return config_data.get('template_files', {})
    except FileNotFoundError:
        print("配置文件未找到，使用默认模板映射")
        return {
            1: 'template_root.html',
            2: 'template_sidebar.html',
            3: 'template_related.html',
            4: 'template_series.html',
            5: 'template_more_tips.html',
            6: 'template_top_articles.html',
            7: 'template_series_top_articles.html'
        }

def generate_html(content, template_type, item_number=None):
    """根据模板类型生成HTML代码"""
    soup = BeautifulSoup(content, 'html.parser')
    try:
        title = soup.find('title').text
        description = soup.find('meta', {'name': 'description'}).get('content', '')
        url = soup.find('link', {'rel': 'canonical'}).get('href', '')
        category = url.split('/')[3].upper() if url else "UNKNOWN"
        url = url.replace("https://www.shareus.com/", "") if url else ""
        date_elem = soup.find('p', class_='posted_date')
        date = date_elem.text.strip() if date_elem else ""
        img_tag = soup.find('img', class_='feature_img')
        # 获取脚本或可执行文件目录
        if getattr(sys, 'frozen', False):
            base_dir = sys._MEIPASS
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))
        if not img_tag:
            print(f"警告: 文件 {url} 的首图可能为视频或无首图，无法提取图片，请手动处理")
            img_src = "default-image.webp"
            if getattr(sys, 'frozen', False):
                default_img_path = os.path.join(sys._MEIPASS, 'images', img_src)
            else:
                script_dir = os.path.dirname(os.path.abspath(__file__))
                default_img_path = os.path.join(script_dir, 'images', img_src)
            if not os.path.exists(default_img_path):
                print(f"警告: 默认图片 {default_img_path} 不存在，请检查资源路径")
        else:
            img_src = img_tag['src'].replace("../", "").replace(".webp", "-m.webp")
        date_formatted = convert_date(date)

        # 模板文件映射
        template_files = load_template_files()  # 从 config.json 加载
        # 确保 template_type 是字符串，因为 JSON 键是字符串
        template_name = template_files.get(str(template_type))
        if not template_name:
            raise ValueError(f'无效的模板类型: {template_type}')

        # 根据是否打包动态设置模板路径
        if getattr(sys, 'frozen', False):
            # 打包后的临时目录
            template_path = os.path.join(sys._MEIPASS, 'templates', template_name)
        else:
            # 开发环境
            script_dir = os.path.dirname(os.path.abspath(__file__))
            template_path = os.path.join(script_dir, 'templates', template_name)

        # 检查模板文件是否存在
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"模板文件未找到: {template_path}")

        # 读取模板文件
        with open(template_path, 'r', encoding='utf-8') as file:
            template = file.read()

        # 根据模板类型调整URL和图片路径
        if template_type in [2, 3, 4, 7]:
            url = '../' + url
            if template_type == 7:
                url = url.split('/')[-1]
            img_src = '../' + img_src
            if template_type == 4:
                img_src = img_src.replace("m.webp", "s.webp")

        # 替换占位符
        html_code = template.format(
            url=url,
            category=category,
            img_src=img_src,
            title=title,
            datetime=date_formatted,
            date=date,
            description=description,
            item_number=item_number if template_type == 6 else ''
        )
        return html_code
    except AttributeError as e:
        print(f"HTML解析错误: {e} - 内容可能缺少必要的标签")
        return ""

def process_files(file_list_path, template_type):
    """处理文件并生成HTML"""
    paths = read_file_paths(file_list_path)
    if template_type == 1 and len(paths) > 10:
        raise TooManyFilesError("根目录文章数量超过10个限制")
    outputs = []
    for index, path in enumerate(paths, start=1):
        try:
            content = get_file_content(path)
            html_code = generate_html(content, template_type, index if template_type == 6 else None)
            if html_code:
                outputs.append(html_code)
        except Exception as e:
            print(f"处理文件 {path} 时出错: {e}")

    if template_type == 1:
        outputs.reverse()

    for output in outputs:
        print(output)

if __name__ == "__main__":
    # 获取可执行文件或脚本目录
    if getattr(sys, 'frozen', False):
        script_dir = os.path.dirname(sys.executable)
    else:
        script_dir = os.path.dirname(os.path.abspath(__file__))
    file_list_path = os.path.join(script_dir, 'urls.txt')
    try:
        template_choice = input("请选择你要生成的网页链接类型:\n1. 根目录最新文章\n2. 侧边栏最新文章\n3. 相关文章\n4. 各系列index\n5. More Software and Computer Usage Tips\n6. 首页的三个顶部文章\n7. 各系列index的三个顶部文章\n选择（1/2/3/4/5/6/7，默认3）: ")
        template_choice = int(template_choice) if template_choice else 3
        if template_choice not in range(1, 8):
            raise ValueError(f"无效的选择: {template_choice}")
        process_files(file_list_path, template_choice)
        input("按回车键退出...")
    except ValueError as e:
        print(f"输入错误: {e}. 请输入有效的数字（1-7）")
    except TooManyFilesError as e:
        print(f"错误: {e}")
    except FileNotFoundError as e:
        print(f"错误: {e}")
    except Exception as e:
        print(f"发生未知错误: {e}")
        
'''
修改说明：
路径处理：使用 sys.executable（打包后）或 __file__（开发时）动态获取程序目录，确保 urls.txt 和 config.json 从外部读取。
模板访问：使用 sys._MEIPASS（打包后）或脚本目录（开发时）访问嵌入的 templates 文件夹。
将 template_type 转换为字符串（str(template_type)），以匹配 config.json 中的键。
健壮性：保留了您的错误处理逻辑，并确保路径在不同环境下都能正确解析。
'''