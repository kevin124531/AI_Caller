"""Generate a sample contacts CSV for local development."""
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

OUTPUT = Path("data/contacts/contacts.csv")
SAMPLE_DATA = [
    {"name": "Alice Johnson", "phone": "+12025550101", "survey_topic": "your onboarding experience", "week_label": "this week"},
    {"name": "Bob Smith",     "phone": "+12025550102", "survey_topic": "your recent support ticket",  "week_label": "this week"},
    {"name": "Carol White",   "phone": "+12025550103", "survey_topic": "your mobile app experience",  "week_label": "this week"},
    {"name": "David Lee",     "phone": "+12025550104", "survey_topic": "your billing experience",     "week_label": "this week"},
    {"name": "Eva Martinez",  "phone": "+12025550105", "survey_topic": "your overall satisfaction",   "week_label": "this week"},
]

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
with open(OUTPUT, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=SAMPLE_DATA[0].keys())
    writer.writeheader()
    writer.writerows(SAMPLE_DATA)

print(f"Sample contacts written to {OUTPUT} ({len(SAMPLE_DATA)} rows)")
