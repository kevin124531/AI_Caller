import csv
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = {"phone", "name"}


def read_contacts(csv_path: str | Path) -> list[dict[str, Any]]:
    """Parse a contacts CSV into a list of contact dicts.

    Required columns: name, phone
    Optional columns: any extra column is passed as dynamic_variables.
    """
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"Contacts CSV not found: {path}")

    contacts: list[dict[str, Any]] = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        columns = set(reader.fieldnames or [])
        missing = REQUIRED_COLUMNS - columns
        if missing:
            raise ValueError(f"Contacts CSV missing required columns: {missing}")

        for row in reader:
            phone = row["phone"].strip()
            name = row["name"].strip()
            if not phone or not name:
                logger.warning("Skipping row with empty phone/name: %s", row)
                continue
            extra = {k: v for k, v in row.items() if k not in REQUIRED_COLUMNS}
            contacts.append({"name": name, "phone": phone, "metadata": extra})

    logger.info("Loaded %d contacts from %s", len(contacts), path)
    return contacts
