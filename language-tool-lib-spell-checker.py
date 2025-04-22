import os
import json
import logging
import csv
from bs4 import BeautifulSoup
import language_tool_python
from tqdm import tqdm
from datetime import datetime


# def calculate_priority(context):
#     lc = context.lower()
#     if '<title>' in lc or '<meta' in lc or '<h1' in lc:
#         return 10
#     elif 'introduction' in lc or 'summary' in lc or 'conclusion' in lc:
#         return 8
#     elif 'footer' in lc or 'copyright' in lc or 'related posts' in lc:
#         return 2
#     else:
#         return 5
def calculate_priority(context):
    lc = context.lower()
    if 'title' in lc or 'meta' in lc or 'main topic' in lc:
        return 10
    elif 'introduction' in lc or 'summary' in lc or 'conclusion' in lc:
        return 8
    elif 'footer' in lc or 'copyright' in lc or 'related posts' in lc:
        return 2
    else:
        return 5


def detect_glossary_hit(context, glossary_terms):
    return any(term.lower() in context.lower() for term in glossary_terms)


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

    glossary_terms = config.get("glossary", [])

    checker.processed_files = checker.load_processed_files()
    folder_path = config.get("input_directory", ".")
    max_len = config.get("max_characters_per_file", 10000)

    file_errors = {}
    type_errors = {}
    csv_rows = []

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

                    context = match.context
                    score = calculate_priority(context)
                    hit = detect_glossary_hit(context, glossary_terms)

                    error_info = {
                        "message": match.message,
                        "context": context,
                        "offset": match.offset,
                        "length": match.errorLength,
                        "suggestions": match.replacements,
                        "priority_score": score,
                        "term_hit": hit
                    }

                    file_errors.setdefault(filename, []).append(error_info)
                    type_errors.setdefault(match.message, set()).add(filename)

                    csv_rows.append({
                        "File": filename,
                        "Message": match.message,
                        "Context": context.replace('\n', ' ').strip(),
                        "Offset": match.offset,
                        "Length": match.errorLength,
                        "Suggestions": ", ".join(match.replacements) or "(no suggestions)",
                        "Priority": str(score),
                        "TermMatched": hit
                    })

                checker.processed_files.add(file_path)
        except Exception as e:
            logging.error(f"Error processing {file_path}: {e}")

    checker.save_processed_files()
    checker.close()

    type_errors = {msg: list(files) for msg, files in type_errors.items()}

    output_data = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "by_file": file_errors,
        "by_error_type": type_errors
    }
    with open("spell_report.json", "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    with open("correction_suggestions.csv", "w", encoding="utf-8", newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            "File", "Message", "Context", "Offset", "Length", "Suggestions", "Priority", "TermMatched"])
        writer.writeheader()
        writer.writerows(csv_rows)

    print("✅ spell_report.json and correction_suggestions.csv generated successfully.")


if __name__ == "__main__":
    config = load_config()
    process_files(config)