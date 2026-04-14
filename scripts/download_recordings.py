"""
Download MP3 recordings for a completed Retell batch call.

Usage:
    # Uses the last batch_call_id saved by the scheduler:
    python scripts/download_recordings.py

    # Or pass a specific batch_call_id:
    python scripts/download_recordings.py --batch-id batch_abc123

    # Or download a single call by call_id:
    python scripts/download_recordings.py --call-id call_xyz456

Recordings are saved to data/recordings/<call_id>.mp3
"""
import argparse
import json
import logging
import sys
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).parent.parent))
from config.settings import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s — %(message)s",
)
logger = logging.getLogger(__name__)

STATE_FILE = Path("data/state/last_batch.json")
RETELL_BASE = "https://api.retellai.com"


def get_headers() -> dict:
    return {"Authorization": f"Bearer {settings.retell_api_key}"}


def list_calls_for_batch(batch_call_id: str) -> list[dict]:
    """Fetch all calls belonging to a batch."""
    logger.info("Fetching calls for batch_call_id=%s", batch_call_id)
    response = httpx.post(
        f"{RETELL_BASE}/v2/list-calls",
        headers=get_headers(),
        json={"filter_criteria": {"batch_call_id": [batch_call_id]}},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def get_call(call_id: str) -> dict:
    """Fetch a single call by ID."""
    response = httpx.get(
        f"{RETELL_BASE}/v2/get-call/{call_id}",
        headers=get_headers(),
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def download_recording(call: dict, output_dir: Path) -> None:
    """Download the recording for a single call if available."""
    call_id = call.get("call_id", "unknown")
    recording_url = call.get("recording_url")

    if not recording_url:
        status = call.get("call_status", "unknown")
        logger.warning("No recording URL for call %s (status: %s) — skipping.", call_id, status)
        return

    out_path = output_dir / f"{call_id}.mp3"
    if out_path.exists():
        logger.info("Already downloaded: %s — skipping.", out_path.name)
        return

    logger.info("Downloading %s → %s", call_id, out_path)
    with httpx.stream("GET", recording_url, timeout=120, follow_redirects=True) as r:
        r.raise_for_status()
        with open(out_path, "wb") as f:
            for chunk in r.iter_bytes(chunk_size=8192):
                f.write(chunk)

    size_kb = out_path.stat().st_size // 1024
    logger.info("Saved %s (%d KB)", out_path.name, size_kb)


def main() -> None:
    parser = argparse.ArgumentParser(description="Download Retell call recordings.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--batch-id", help="Retell batch_call_id to download recordings for")
    group.add_argument("--call-id", help="Single Retell call_id to download")
    args = parser.parse_args()

    output_dir = Path(settings.recordings_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.call_id:
        call = get_call(args.call_id)
        download_recording(call, output_dir)
        return

    # Resolve batch_call_id
    batch_call_id = args.batch_id
    if not batch_call_id:
        if not STATE_FILE.exists():
            logger.error(
                "No batch_call_id provided and no state file found at %s.\n"
                "Run the scheduler first, or pass --batch-id manually.",
                STATE_FILE,
            )
            sys.exit(1)
        state = json.loads(STATE_FILE.read_text())
        batch_call_id = state["batch_call_id"]
        logger.info("Using saved batch_call_id: %s", batch_call_id)

    calls = list_calls_for_batch(batch_call_id)
    if not calls:
        logger.warning("No calls found for batch %s.", batch_call_id)
        return

    logger.info("Found %d call(s). Downloading recordings...", len(calls))
    downloaded = 0
    skipped = 0
    for call in calls:
        status = call.get("call_status", "")
        if status not in ("ended", "error"):
            logger.info("Call %s status=%s — not yet ended, skipping.", call.get("call_id"), status)
            skipped += 1
            continue
        if call.get("recording_url"):
            download_recording(call, output_dir)
            downloaded += 1
        else:
            logger.warning("Call %s has no recording URL.", call.get("call_id"))
            skipped += 1

    logger.info("Done. Downloaded: %d  Skipped: %d", downloaded, skipped)


if __name__ == "__main__":
    main()
