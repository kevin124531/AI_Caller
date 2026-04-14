"""Generate a sample contacts CSV for local development/testing."""
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

OUTPUT = Path("data/contacts/contacts.csv")

# question_category must match one of the five categories in agent/system_prompt.py:
#   Data Center Design & Operations
#   Sustainability & Environmental Impact
#   Digital Infrastructure & Networking
#   Industry Trends & Future Outlook
#   Leadership, Strategy & Decision-Making
SAMPLE_DATA = [
    {"name": "Alice Johnson", "phone": "+12025550101", "question_category": "Data Center Design & Operations"},
    {"name": "Bob Smith",     "phone": "+12025550102", "question_category": "Sustainability & Environmental Impact"},
    {"name": "Carol White",   "phone": "+12025550103", "question_category": "Digital Infrastructure & Networking"},
    {"name": "David Lee",     "phone": "+12025550104", "question_category": "Industry Trends & Future Outlook"},
    {"name": "Eva Martinez",  "phone": "+12025550105", "question_category": "Leadership, Strategy & Decision-Making"},
]

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
with open(OUTPUT, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=SAMPLE_DATA[0].keys())
    writer.writeheader()
    writer.writerows(SAMPLE_DATA)

print(f"Sample contacts written to {OUTPUT} ({len(SAMPLE_DATA)} rows)")
