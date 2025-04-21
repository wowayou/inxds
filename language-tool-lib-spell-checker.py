import os
import json
import logging
from bs4 import BeautifulSoup
import language_tool_python
from tqdm import tqdm
from datetime import datetime


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

                    # 构建错误信息结构
                    error_info = {
                        "message": match.message,
                        "context": match.context,
                        "offset": match.offset,
                        "length": match.errorLength,
                        "suggestions": match.replacements
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


if __name__ == "__main__":
    config = load_config()
    process_files(config)
    