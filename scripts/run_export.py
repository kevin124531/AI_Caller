"""One-shot: export unexported transcripts as training JSONL."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from formatter.export_job import export_training_data

if __name__ == "__main__":
    out = asyncio.run(export_training_data())
    print(f"Export written to: {out}")
