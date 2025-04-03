import os
from typing import List, Optional, Dict
import json
import html
from bs4 import BeautifulSoup
from datetime import datetime
import tkinter as tk
from tkinter import filedialog, messagebox
import logging

# Load configuration from config.json
try:
    with open('config.json', 'r', encoding='utf-8') as f:
        CONFIG = json.load(f)
except FileNotFoundError:
    CONFIG = {
        "template_path": "templates.py",
        "default_dir": os.path.expanduser("~"),
        "max_files": {"1": 10, "2": 9, "6": 3},
        "log_file": "html_generator.log"
    }
    with open('config.json', 'w', encoding='utf-8') as f:
        json.dump(CONFIG, f, indent=4)

# Configure logging to overwrite the log file each run
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename=CONFIG["log_file"],
    filemode='w'  # 每次运行时覆盖日志文件
)

from templates import TEMPLATES  # type: ignore

class TooManyFilesError(Exception):
    """Custom exception for exceeding file count limit."""
    pass

def read_file_paths(file_path: str) -> List[str]:
    """
    Read and normalize file paths from a text file.
    
    Args:
        file_path: Path to the file containing list of paths
        
    Returns:
        List of normalized file paths
        
    Raises:
        Exception: If file cannot be decoded with any supported encoding
    """
    encodings = ['utf-8', 'gbk', 'iso-8859-1']
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as file:
                return [
                    os.path.normpath(path.strip())
                    for path in file.readlines()
                    if not (path.strip().startswith('#') or path.strip().startswith('//'))
                ]
        except UnicodeDecodeError:
            continue
    raise Exception(f"Cannot decode file {file_path} with available encodings")

def normalize_path(path: str) -> str:
    """规范化路径处理，统一使用正斜杠"""
    return os.path.normpath(path.replace('\\', '/')).replace(os.path.sep, '/')
'''
当前的 normalize_path 函数先用 replace('\', '/') 替换了反斜杠，但紧接着使用了 os.path.normpath，该函数会根据当前系统返回系统默认的路径分隔符（在 Windows 上就是反斜杠）。解决方法是对 os.path.normpath 的结果再次替换回正斜杠
'''

def get_file_content(path: str) -> str:
    """
    Read content from a file with multiple encoding attempts.
    
    Args:
        path: Path to the file
        
    Returns:
        File content as string
        
    Raises:
        Exception: If file cannot be decoded
    """
    encodings = ['utf-8', 'gbk', 'iso-8859-1']
    for encoding in encodings:
        try:
            with open(path, 'r', encoding=encoding) as file:
                return file.read()
        except UnicodeDecodeError:
            continue
    raise Exception(f"Cannot decode file {path} with available encodings")

def convert_date(date_str: str) -> str:
    """
    Convert date string to YYYY-MM-DD format.
    
    Args:
        date_str: Date string in various formats
        
    Returns:
        Formatted date string or original if conversion fails
    """
    formats = ['%B %d, %Y', '%B %d %Y', '%B %d,%Y', '%B %d %Y', '%b %d, %Y', '%b %d %Y']
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).strftime('%Y-%m-%d')
        except ValueError:
            continue
    logging.warning(f"Date conversion failed for '{date_str}'")
    return date_str

def adjust_paths_for_template(metadata: Dict[str, str], template_type: int) -> Dict[str, str]:
    """根据模板类型调整路径，并统一格式化为正斜杠"""
    if template_type in [2, 3, 4, 7]:
        if template_type in [4, 7]:
            # 对于模板4和7，只保留文件名（利用 os.path.basename 直接获取文件名） 因为肯定隶属同一个目录（但需要注意不要粘贴错了目录）
            metadata['url'] = os.path.basename(metadata['url'])
        else:
            metadata['url'] = '../' + metadata['url']
        metadata['img_src'] = '../' + metadata['img_src']
        if template_type == 4:
            metadata['img_src'] = metadata['img_src'].replace("m.webp", "s.webp")
    # 统一使用 normalize_path 规范化路径（将所有反斜杠替换为正斜杠）
    metadata['url'] = normalize_path(metadata['url'])
    metadata['img_src'] = normalize_path(metadata['img_src'])
    return metadata

def process_image(img_tag, url: str) -> str:
    """处理图片路径"""
    if not img_tag:
        logging.warning(f"文件 {url} 的首图可能为视频或无首图")
        return "default-image.webp"
    # 先处理路径中的 ../ ，再规范化路径分隔符
    return normalize_path(img_tag['src'].replace("../", "").replace(".webp", "-m.webp"))

def parse_article_metadata(soup: BeautifulSoup, file_path: str) -> Optional[Dict[str, str]]:
    """解析文章元数据"""
    try:
        title = soup.find('title').text
        description = soup.find('meta', {'name': 'description'}).get('content', '')
        url = soup.find('link', {'rel': 'canonical'}).get('href', '')
        
        return {
            'title': title,
            'description': description,
            'url': normalize_path(url.replace("https://www.shareus.com/", "")),
            'category': url.split('/')[3].upper() if url and len(url.split('/')) > 3 else "UNKNOWN",
            'date': convert_date(soup.find('p', class_='posted_date').text.strip()) 
                    if soup.find('p', class_='posted_date') else "",
            'img_src': process_image(soup.find('img', class_='feature_img'), file_path)
        }
    except AttributeError as e:
        logging.error(f"HTML解析错误: {e}")
        return None

def generate_html(content: str, template_type: int, item_number: Optional[int] = None) -> str:
    """生成HTML代码"""
    soup = BeautifulSoup(content, 'html.parser')
    metadata = parse_article_metadata(soup, content)
    if not metadata:
        return ""
    
    metadata = adjust_paths_for_template(metadata, template_type)
    
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
        # alt_title 采用与 title 相同的转义逻辑，并对引号和 & 进行额外替换
        'alt_title': html.escape(metadata['title']).replace('"', '&quot;').replace('&', '&amp;')
    }

    # 根据模板类型获取模板（模板类型7采用默认模板）
    template = TEMPLATES.get(template_type)
    if isinstance(template, dict):
        template = template.get('default', '')
    return template.format(**escaped_data) if template else ""

def process_files(file_paths: List[str], template_type: int) -> None:
    """
    Process list of files and generate HTML output.
    
    Args:
        file_paths: List of file paths to process
        template_type: Template number to use
        
    Raises:
        TooManyFilesError: If file count exceeds template-specific limit
    """
    max_files = CONFIG["max_files"].get(str(template_type), float('inf'))
    if len(file_paths) > max_files:
        raise TooManyFilesError(f"File count ({len(file_paths)}) exceeds limit ({max_files}) for template {template_type}")

    outputs = []
    for index, path in enumerate(file_paths, start=1):
        try:
            content = get_file_content(path)
            html_output = generate_html(content, template_type, index if template_type == 6 else None)
            if html_output:
                outputs.append(html_output)
        except Exception as e:
            logging.error(f"Error processing file {path}: {e}")

    if template_type == 1:
        outputs.reverse()
    
    for output in outputs:
        print(output)

def select_files() -> List[str]:
    """
    Open file dialog for selecting HTML files.
    
    Returns:
        List of selected file paths
    """
    root = tk.Tk()
    root.withdraw()
    files = filedialog.askopenfilenames(
        title="选择HTML文件",
        filetypes=[("HTML files", "*.html"), ("All files", "*.*")],
        initialdir=CONFIG["default_dir"],
        multiple=True
    )
    root.quit()
    valid_paths = [path for path in files if path.lower().endswith('.html')]
    if not valid_paths:
        messagebox.showerror("错误", "没有选择有效的HTML文件")
    return valid_paths

def main() -> None:
    """Main program execution."""
    try:
        while True:
            choice = input(
                "请选择模板类型:\n1. 根目录最新文章\n2. 侧边栏最新文章\n3. 相关文章\n"
                "4. 各系列index\n5. More Software Tips\n6. 首页顶部文章\n7. 各系列index顶部文章\n选择（1-7）或'q'退出: "
            ).strip()
            
            if choice.lower() == 'q':
                print("程序退出")
                return
            
            try:
                template_type = int(choice)
                if template_type not in range(1, 8):
                    print("请输入1-7之间的数字")
                    continue
                break
            except ValueError:
                print("请输入有效的数字")

        file_paths = select_files()
        if not file_paths:
            print("未选择文件，程序退出")
            return

        print(f"选中的文件: {', '.join(file_paths)}")
        if input("确认继续?(y/n): ").lower() != 'y':
            print("用户取消，程序退出")
            return

        process_files(file_paths, template_type)

    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        print(f"发生错误: {e}")

if __name__ == "__main__":
    main()
