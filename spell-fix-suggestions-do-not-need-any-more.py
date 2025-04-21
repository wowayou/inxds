import json
import os
import csv
from datetime import datetime

REPORT_FILE = "spell_report.json"
# 生成带时间戳的 CSV 文件名
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
OUTPUT_FILE = f"correction_suggestions_{timestamp}.csv"


def load_report(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def generate_csv_rows(report):
    rows = []
    errors_by_file = report.get("by_file", {})

    for filename, errors in errors_by_file.items():
        for error in errors:
            rows.append({
                "File": filename,
                "Message": error.get('message', ''),
                "Context": error.get('context', '').replace("\n", " ").strip(),
                "Offset": error.get('offset', ''),
                "Length": error.get('length', ''),
                "Suggestions": ", ".join(error.get('suggestions', [])) or "(no suggestions)",
                "Priority": error.get('priority_score', 0)  # 默认为 0，如果没有设置
            })
    return rows


def save_csv(rows, path):
    with open(path, "w", encoding="utf-8", newline='') as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["File", "Message", "Context", "Offset", "Length", "Suggestions", "Priority"]
        )
        writer.writeheader()
        writer.writerows(rows)


def main():
    if not os.path.exists(REPORT_FILE):
        print(f"❌ Cannot find report file: {REPORT_FILE}")
        return

    report = load_report(REPORT_FILE)
    rows = generate_csv_rows(report)

    if not rows:
        print("⚠️ No spelling issues found in the report.")
        return

    save_csv(rows, OUTPUT_FILE)
    print(f"✅ Suggestions written to {OUTPUT_FILE} ({len(rows)} entries)")


if __name__ == "__main__":
    main()
    