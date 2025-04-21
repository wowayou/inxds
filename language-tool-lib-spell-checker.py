import os
import json
import logging
import csv  # ✅ 添加这一行
from bs4 import BeautifulSoup
import language_tool_python
from tqdm import tqdm
from datetime import datetime
import re

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
        except Exception as e:
            logging.warning(f"Failed to load processed_files.txt: {e}")
        return set()

    def save_processed_files(self):
        try:
            with open("processed_files.txt", "w") as f:
                for file in self.processed_files:
                    f.write(file + "\n")
        except Exception as e:
            logging.warning(f"Failed to write processed_files.txt: {e}")

    def check_text(self, text):
        return self.tool.check(text)

    def close(self):
        self.tool.close()

    def calculate_priority(self, context):
        """根据错误内容计算优先级"""
        if re.search(r'(title|<meta|<h1|</h1>)', context):
            return 3  # 高优先级：title, meta, h1
        elif re.search(r'(introduction|conclusion|summary)', context):
            return 2  # 次优先级：正文首段/末段
        elif re.search(r'(footer|copyright|all rights reserved|hidden)', context):
            return 1  # 低优先级：页脚、版权等
        return 0  # 普通优先级：其他内容

class HTMLParser:
    def __init__(self, config):
        self.skip_tags = config.get("skip_tags", [])
        self.skip_words = config.get("skip_words", [])
        self.skip_messages = config.get("skip_messages", [])

    def clean_html(self, soup):
        for tag in self.skip_tags:
            for element in soup.find_all(tag):
                element.decompose()
        return soup.get_text(separator=' ', strip=True)

    def should_skip_error(self, match):
        for skip_msg in self.skip_messages:
            if skip_msg in match.message:
                return True
        if any(word in match.context for word in self.skip_words):
            return True
        return False

def load_config():
    with open('config.json', 'r', encoding='utf-8') as file:
        return json.load(file)

def process_files(config):
    checker = SpellChecker(config)
    parser = HTMLParser(config)

    checker.processed_files = checker.load_processed_files()
    folder_path = config.get("input_directory", ".")
    max_len = config.get("max_characters_per_file", 10000)

    file_errors = {}
    type_errors = {}

    all_files = []
    for root, dirs, files in os.walk(folder_path):
        for filename in files:
            if filename.endswith(".html"):
                full_path = os.path.join(root, filename)
                if full_path not in checker.processed_files:
                    all_files.append(full_path)

    for file_path in tqdm(all_files, desc="Processing files", unit="file"):
        try:
            filename = os.path.relpath(file_path, folder_path)
            with open(file_path, 'r', encoding='utf-8') as file:
                soup = BeautifulSoup(file, "html.parser")
                text = parser.clean_html(soup)

                if len(text) > max_len:
                    continue

                matches = checker.check_text(text)

                for match in matches:
                    if parser.should_skip_error(match):
                        continue

                    # 计算错误优先级
                    priority_score = checker.calculate_priority(match.context)

                    error_info = {
                        "message": match.message,
                        "context": match.context,
                        "offset": match.offset,
                        "length": match.errorLength,
                        "suggestions": match.replacements,
                        "priority_score": priority_score  # 添加优先级评分
                    }

                    # 按文件归类
                    file_errors.setdefault(filename, []).append(error_info)

                    # 按错误类型归类
                    type_errors.setdefault(match.message, set()).add(filename)

                checker.processed_files.add(file_path)
        except Exception as e:
            logging.error(f"Error processing {file_path}: {e}")

    checker.save_processed_files()
    checker.close()

    # 将 set 转成 list 以便序列化
    type_errors = {msg: list(files) for msg, files in type_errors.items()}

    # 输出 JSON
    output_data = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "by_file": file_errors,
        "by_error_type": type_errors
    }
    with open("spell_report.json", "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print("Report saved to spell_report.json")

# 加载 JSON 报告
def load_report(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# 生成 CSV 文件
def generate_csv():
    report = load_report("spell_report.json")
    rows = []

    errors_by_file = report.get("by_file", {})
    for filename, errors in errors_by_file.items():
        for error in errors:
            rows.append({
                "File": filename,
                "Message": error['message'],
                "Context": error['context'],
                "Offset": error['offset'],
                "Length": error['length'],
                "Suggestions": ", ".join(error['suggestions']),
                "Priority": error['priority_score']
            })

    save_csv(rows, "correction_suggestions.csv")

def save_csv(rows, path):
    with open(path, "w", encoding="utf-8", newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["File", "Message", "Context", "Offset", "Length", "Suggestions", "Priority"])
        writer.writeheader()
        writer.writerows(rows)

if __name__ == "__main__":
    config = load_config()
    process_files(config)
    generate_csv()
