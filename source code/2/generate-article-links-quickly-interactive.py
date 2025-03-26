import os
from typing import List, Optional, Dict
import json
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
    filemode='w'  # Added to overwrite log file instead of appending
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

def generate_html(content: str, template_type: int, item_number: Optional[int] = None) -> str:
    """
    Generate HTML code from content using specified template.
    
    Args:
        content: HTML content to parse
        template_type: Template number (1-6)
        item_number: Item position number (for template 6)
        
    Returns:
        Generated HTML string
    """
    soup = BeautifulSoup(content, 'html.parser')
    try:
        title = soup.find('title').text if soup.find('title') else "Untitled"
        description = soup.find('meta', {'name': 'description'}).get('content', 'No description')
        url = soup.find('link', {'rel': 'canonical'}).get('href', '')
        category = url.split('/')[3].upper() if url and len(url.split('/')) > 3 else "UNKNOWN"
        url = url.replace("https://www.shareus.com/", "") if url else ""
        date_elem = soup.find('p', class_='posted_date')
        date = date_elem.text.strip() if date_elem else datetime.now().strftime('%B %d, %Y')
        img_tag = soup.find('img', class_='feature_img')
        img_src = img_tag['src'].replace("../", "").replace(".webp", "-m.webp") if img_tag and 'src' in img_tag.attrs else "default-image.webp"
        date_formatted = convert_date(date)

        template: Dict = TEMPLATES.get(template_type, {})
        if not template:
            raise ValueError(f"Invalid template type: {template_type}")

        template_str = (
            template['with_description'] if template_type == 6 and item_number == 1
            else template['without_description'] if template_type == 6
            else template['default']
        )

        if template_type in [2, 3, 4]:
            url = '../' + url
            img_src = '../' + (img_src.replace("m.webp", "s.webp") if template_type == 4 else img_src)

        return template_str.format(
            url=url, category=category, img_src=img_src, title=title,
            datetime=date_formatted, date=date, description=description,
            item_number=item_number
        )
    except AttributeError as e:
        logging.error(f"Attribute error in HTML parsing: {e}")
        return ""

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
            html = generate_html(content, template_type, index if template_type == 6 else None)
            if html:
                outputs.append(html)
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
                "4. 各系列index\n5. More Software Tips\n6. 首页顶部文章\n选择（1-6）或'q'退出: "
            ).strip()
            
            if choice.lower() == 'q':
                print("程序退出")
                return
            
            try:
                template_type = int(choice)
                if template_type not in range(1, 7):
                    print("请输入1-6之间的数字")
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
# import os
# from bs4 import BeautifulSoup
# from datetime import datetime
# import tkinter as tk
# from tkinter import filedialog
# from tkinter import messagebox
# import logging
# from templates import TEMPLATES  # 导入模板

# # 配置日志
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', filename='html_generator.log')

# class TooManyFilesError(Exception):
#     """Custom exception raised when the number of files exceeds the limit."""
#     pass

# def read_file_paths(file_path):
#     encodings = ['utf-8', 'gbk', 'iso-8859-1']
#     for encoding in encodings:
#         try:
#             file_path = os.path.normpath(file_path)
#             with open(file_path, 'r', encoding=encoding) as file:
#                 return [os.path.normpath(path.strip()) for path in file.readlines() if not (path.strip().startswith('#') or path.strip().startswith('//'))]
#         except UnicodeDecodeError:
#             continue
#     raise Exception(f"Cannot decode file {file_path} with available encodings")

# def get_file_content(path):
#     encodings = ['utf-8', 'gbk', 'iso-8859-1']
#     for encoding in encodings:
#         try:
#             path = os.path.normpath(path)
#             with open(path, 'r', encoding=encoding) as file:
#                 return file.read()
#         except UnicodeDecodeError:
#             continue
#     raise Exception(f"Cannot decode file {path} with available encodings")

# def convert_date(date_str):
#     formats = ['%B %d, %Y', '%B %d %Y', '%B %d,%Y', '%B %d %Y', '%b %d, %Y', '%b %d %Y']
#     for fmt in formats:
#         try:
#             date_obj = datetime.strptime(date_str, fmt)
#             return date_obj.strftime('%Y-%m-%d')
#         except ValueError:
#             continue
#     logging.warning(f"Date conversion error for '{date_str}'")
#     return date_str

# def generate_html(content, template_type, item_number=None):
#     soup = BeautifulSoup(content, 'html.parser')
#     try:
#         title = soup.find('title').text if soup.find('title') else "Untitled"
#         description = soup.find('meta', {'name': 'description'}).get('content', 'No description available')
#         url = soup.find('link', {'rel': 'canonical'}).get('href', '')
#         category = url.split('/')[3].upper() if url and len(url.split('/')) > 3 else "UNKNOWN"
#         url = url.replace("https://www.shareus.com/", "") if url else ""
#         date_elem = soup.find('p', class_='posted_date')
#         date = date_elem.text.strip() if date_elem else datetime.now().strftime('%B %d, %Y')
#         img_tag = soup.find('img', class_='feature_img')
#         img_src = img_tag['src'].replace("../", "").replace(".webp", "-m.webp") if img_tag and 'src' in img_tag.attrs else "default-image.webp"
#         date_formatted = convert_date(date) if date else datetime.now().strftime('%Y-%m-%d')

#         template = TEMPLATES.get(template_type)
#         if not template:
#             raise ValueError('Invalid template type')

#         if template_type == 6:
#             if item_number == 1:
#                 template_str = template['with_description']
#             else:
#                 template_str = template['without_description']
#         else:
#             template_str = template['default']

#         # 动态调整 URL 和 img_src
#         if template_type in [2, 3, 4]:
#             url = '../' + url
#             img_src = '../' + (img_src.replace("m.webp", "s.webp") if template_type == 4 else img_src)

#         return template_str.format(url=url, category=category, img_src=img_src, title=title, 
#                                  datetime=date_formatted, date=date, description=description, 
#                                  item_number=item_number)
#     except AttributeError as e:
#         logging.error(f"Attribute error in HTML parsing for content: {e}")
#         return ""

# def process_files(file_paths, template_type):
#     if template_type == 1 and len(file_paths) > 10:
#         raise TooManyFilesError("The number of files exceeds the limit of 10 for root directory articles.")
#     if template_type == 6 and len(file_paths) > 3:
#         raise TooManyFilesError("The number of files for top articles (template 6) exceeds the limit of 3.")
    
#     outputs = []
#     for index, path in enumerate(file_paths, start=1):
#         try:
#             content = get_file_content(path)
#             html_code = generate_html(content, template_type, index if template_type == 6 else None)
#             if html_code:
#                 outputs.append(html_code)
#         except Exception as e:
#             logging.error(f"Error processing file {path}: {e}")
    
#     if template_type == 1:  # 根目录最新文章时逆序输出
#         outputs.reverse()
    
#     for output in outputs:
#         print(output)

# def select_files():
#     print("请选择需要生成HTML的HTML文件（支持跨目录选择，按住Ctrl键可多选）。")
#     root = tk.Tk()
#     root.withdraw()
#     # initial_dir = os.path.expanduser("~")  # 默认用户主目录
#     file_paths = filedialog.askopenfilenames(
#         title="选择HTML文件",
#         filetypes=[("HTML files", "*.html"), ("All files", "*.*")],
#         # initialdir=initial_dir,
#         multiple=True
#     )
#     root.quit()
#     # 过滤只保留 .html 文件
#     valid_paths = [path for path in file_paths if path.lower().endswith('.html')]
#     if not valid_paths:
#         messagebox.showerror("错误", "没有选择有效的HTML文件。")
#         return []
#     return valid_paths

# def get_user_confirmation():
#     confirmation = input("确认继续处理这些文件吗？(y/n): ").lower()
#     return confirmation == 'y'

# if __name__ == "__main__":
#     try:
#         while True:
#             template_choice = input("请选择你要生成的网页链接类型:\n1. 根目录最新文章\n2. 侧边栏最新文章\n3. 相关文章\n4. 各系列index\n5. More Software and Computer Usage Tips\n6. 首页的三个顶部文章\n选择（1/2/3/4/5/6）, 输入 'q' 来退出: ").strip()
            
#             if template_choice.lower() == 'q':
#                 print("程序退出。")
#                 break
            
#             try:
#                 template_choice = int(template_choice)
#                 if template_choice not in [1, 2, 3, 4, 5, 6]:
#                     print("无效的输入，请输入1-6之间的数字。")
#                     continue
#                 break
#             except ValueError:
#                 print("无效的输入，请输入数字1-6。")

#         file_paths = select_files()
#         if not file_paths:
#             print("没有选择文件。程序退出。")
#             exit()

#         print(f"选中的文件: {', '.join(file_paths)}")
#         if not get_user_confirmation():
#             print("用户取消操作。程序退出。")
#             exit()

#         process_files(file_paths, template_choice)

#     except ValueError as e:
#         print(f"输入错误: {e}. 请输入有效的数字。")
#     except TooManyFilesError as e:
#         print(f"错误: {e}")
#     except Exception as e:
#         logging.error(f"发生了意外的错误: {e}")