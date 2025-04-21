import json
import os
import csv
from datetime import datetime

REPORT_FILE = "spell_report.json"
OUTPUT_FILE = "correction_suggestions.csv"


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
                "Message": error['message'],
                "Context": error['context'].replace("\n", " ").strip(),
                "Offset": error['offset'],
                "Length": error['length'],
                "Suggestions": ", ".join(error['suggestions']) or "(no suggestions)"
            })
    return rows


def save_csv(rows, path):
    with open(path, "w", encoding="utf-8", newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["File", "Message", "Context", "Offset", "Length", "Suggestions"])
        writer.writeheader()
        writer.writerows(rows)


def main():
    if not os.path.exists(REPORT_FILE):
        print(f"❌ Cannot find report file: {REPORT_FILE}")
        return

    report = load_report(REPORT_FILE)
    rows = generate_csv_rows(report)
    save_csv(rows, OUTPUT_FILE)

    print(f"✅ Suggestions written to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
