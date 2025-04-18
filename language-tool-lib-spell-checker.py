import os
import json
import logging
from bs4 import BeautifulSoup
import language_tool_python
from tqdm import tqdm
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


class SpellChecker:
    def __init__(self, config):
        self.tool = language_tool_python.LanguageTool('en-US')
        self.config = config
        self.processed_files = set()

    def load_processed_files(self):
        try:
            if os.path.exists("processed_files.txt"):
                with open("processed_files.txt", "r") as f:
                    return set(line.strip() for line in f.readlines())
        except PermissionError:
            logging.error("Permission denied while trying to read 'processed_files.txt'")
        return set()

    def save_processed_files(self):
        try:
            with open("processed_files.txt", "w") as f:
                for file in self.processed_files:
                    f.write(file + "\n")
        except PermissionError:
            logging.error("Permission denied while trying to write to 'processed_files.txt'")

    def check_text(self, text):
        return self.tool.check(text)

    def close(self):
        self.tool.close()


class HTMLParser:
    def __init__(self, config):
        self.skip_tags = config["skip_tags"]
        self.skip_words = config["skip_words"]
        self.skip_messages = config["skip_messages"]

    def clean_html(self, soup):
        """移除指定的标签，并返回清理后的文本"""
        for tag in self.skip_tags:
            for element in soup.find_all(tag):
                element.decompose()
        return soup.get_text(separator=' ', strip=True)

    def should_skip_error(self, match):
        """判断该错误是否需要跳过"""
        for skip_message in self.skip_messages:
            if skip_message in match.message:  # 使用in来进行模糊匹配
                return True
        if any(word in match.context for word in self.skip_words):
            return True
        return False


class ReportGenerator:
    def __init__(self, filename):
        self.pdf_file = canvas.Canvas(filename, pagesize=letter)
        self.pdf_file.setFont("Helvetica", 10)
        self.y_position = 690
        self.page_width, self.page_height = letter  # 获取页面尺寸

    def write_header(self, current_time):
        self.pdf_file.drawString(100, 750, f"Spell Check Report generated on {current_time}")
        self.pdf_file.drawString(100, 735, "===============================================")
        self.pdf_file.drawString(100, 720, "Errors and Suggestions:")
        self.pdf_file.drawString(100, 705, "===============================================")

    def write_error(self, filename, match):
        """写入拼写错误信息"""
        self.pdf_file.drawString(100, self.y_position, f"--- Errors in file: {filename} ---")
        self.y_position -= 15
        self.pdf_file.drawString(100, self.y_position, f"Error: {match.context}")
        self.y_position -= 15
        self.pdf_file.drawString(100, self.y_position, f"Location: {match.offset} - {match.offset + match.errorLength}")
        self.y_position -= 15
        self.pdf_file.drawString(100, self.y_position, f"Problem: {match.message}")
        self.y_position -= 15
        self.pdf_file.drawString(100, self.y_position, f"Suggested correction(s): {', '.join(match.replacements)}")
        self.y_position -= 30
        
        # 检查是否超出页面，如果超出则创建新的一页
        if self.y_position < 100:
            self.pdf_file.showPage()  # 创建新的一页
            self.pdf_file.setFont("Helvetica", 10)  # 重新设置字体
            self.y_position = 750  # 重置 y_position

    def finalize_report(self, current_time):
        self.pdf_file.drawString(100, self.y_position, "===============================================")
        self.pdf_file.drawString(100, self.y_position - 15, f"Spell Check Completed on {current_time}")
        self.pdf_file.drawString(100, self.y_position - 30, "===============================================")
        self.pdf_file.save()


def load_config():
    with open('config.json', 'r') as file:
        return json.load(file)


def process_files(config):
    checker = SpellChecker(config)
    parser = HTMLParser(config)
    report = ReportGenerator(f"spell_check_report_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.pdf")

    # 获取上次处理的文件进度
    checker.processed_files = checker.load_processed_files()

    # 创建报告头部
    report.write_header(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    # 遍历文件夹及子文件夹中的所有HTML文件
    folder_path = 'D:/cg/shareus_web/trunk/'  # 替换为你的文件夹路径
    all_files = []

    for root, dirs, files in os.walk(folder_path):
        for filename in files:
            if filename.endswith(".html"):  # 只处理HTML文件
                file_path = os.path.join(root, filename)
                if file_path in checker.processed_files:
                    continue  # 如果文件已经处理过，则跳过
                all_files.append(file_path)

    # 处理每个文件
    for file_path in tqdm(all_files, desc="Processing files", unit="file"):
        try:
            filename = os.path.basename(file_path)
            with open(file_path, 'r', encoding='utf-8') as file:
                soup = BeautifulSoup(file, "html.parser")
                text = parser.clean_html(soup)

                if len(text) > config["max_characters_per_file"]:
                    continue  # 如果文件内容过长，跳过该文件

                matches = checker.check_text(text)

                if matches:
                    for match in matches:
                        if not parser.should_skip_error(match):
                            report.write_error(filename, match)
                    checker.processed_files.add(file_path)
                    checker.save_processed_files()  # 保存进度
        except Exception as e:
            logging.error(f"Error processing {file_path}: {e}")
            continue

    # 完成报告
    report.finalize_report(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    checker.close()
    print(f"Report has been generated and saved as {report.pdf_file._filename}")


if __name__ == "__main__":
    config = load_config()
    process_files(config)

'''
代码解释：
模块化设计：

SpellChecker：负责拼写检查的相关功能。

HTMLParser：负责处理 HTML 页面，包括提取文本和跳过指定标签、单词等。

ReportGenerator：负责生成 PDF 报告文件，包含写入错误信息的逻辑。

配置文件：

使用 JSON 格式的配置文件 config.json 来存储可调节参数，如跳过的单词、错误类型、标签等。这样做能够更灵活地调整设置，而无需修改代码。

跳过指定内容：

跳过特定单词：通过在 HTMLParser 中检查上下文中的单词来跳过自定义单词。

跳过特定问题：通过在 SpellChecker 中检查错误消息来跳过特定问题（如风格问题）。

跳过代码片段：在 clean_html 方法中，移除了 <code> 标签的内容，确保代码部分不参与拼写检查。

增强 HTML 页面处理：

更灵活地处理各种 HTML 标签，增强了对复杂页面结构的适应性。

总结：
通过模块化设计、使用配置文件来管理参数以及增强 HTML 解析能力，我们显著提高了脚本的灵活性、可扩展性和可维护性。现在，脚本能够处理不同类型的 HTML 页面，灵活地跳过自定义单词、特定拼写错误以及代码片段。同时，代码的耦合度降低，容易进行功能扩展和修改。
'''