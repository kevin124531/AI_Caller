"""One-shot: create all database tables."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from store.database import create_all_tables

if __name__ == "__main__":
    asyncio.run(create_all_tables())
    print("Tables created.")
