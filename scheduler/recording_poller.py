"""
Background poller — watches a batch call and, as each call finishes:
  1. Downloads the MP3 recording to data/recordings/
  2. Transcribes it with AssemblyAI (speaker diarization)
  3. Appends training pairs to data/exports/training.jsonl

Launched automatically by weekly_job.py after a batch is dispatched.
Polls every POLL_INTERVAL_SECONDS until all calls are done or MAX_WAIT_MINUTES elapses.
"""
import asyncio
import logging
from pathlib import Path

import httpx

from config.settings import settings

logger = logging.getLogger(__name__)

POLL_INTERVAL_SECONDS = 120   # check every 2 minutes
MAX_WAIT_MINUTES = 180        # give up after 3 hours
TERMINAL_STATUSES = {"ended", "error"}

RETELL_BASE = "https://api.retellai.com"


def _headers() -> dict:
    return {"Authorization": f"Bearer {settings.retell_api_key}"}


async def _list_calls(client: httpx.AsyncClient, batch_call_id: str) -> list[dict]:
    response = await client.post(
        f"{RETELL_BASE}/v2/list-calls",
        headers=_headers(),
        json={"filter_criteria": {"batch_call_id": [batch_call_id]}},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


async def _download_mp3(client: httpx.AsyncClient, recording_url: str, out_path: Path) -> None:
    """Stream download a recording URL to out_path."""
    async with client.stream("GET", recording_url, timeout=120, follow_redirects=True) as r:
        r.raise_for_status()
        with open(out_path, "wb") as f:
            async for chunk in r.aiter_bytes(chunk_size=8192):
                f.write(chunk)


def _transcribe_and_format(mp3_path: Path, call_id: str, metadata: dict) -> None:
    """
    Synchronous worker (runs in a thread pool):
      1. Transcribe the MP3 with AssemblyAI.
      2. Append training pairs to training.jsonl.
    """
    from transcriber.audio_transcriber import transcribe_call
    from formatter.qwen_formatter import append_to_jsonl

    try:
        transcript_data = transcribe_call(mp3_path, call_id)
        pairs = append_to_jsonl(transcript_data, metadata)
        logger.info("call %s → %d training pair(s) added.", call_id, pairs)
    except Exception as exc:
        logger.error("Transcription/formatting failed for call %s: %s", call_id, exc)


async def _process_call(client: httpx.AsyncClient, call: dict, recordings_dir: Path) -> bool:
    """
    Download, transcribe, and format a single completed call.
    Returns True if the MP3 was newly downloaded.
    """
    call_id = call.get("call_id", "unknown")
    recording_url = call.get("recording_url")

    if not recording_url:
        logger.warning("Call %s has no recording URL — skipping.", call_id)
        return False

    mp3_path = recordings_dir / f"{call_id}.mp3"

    if not mp3_path.exists():
        logger.info("Downloading recording for call %s...", call_id)
        await _download_mp3(client, recording_url, mp3_path)
        size_kb = mp3_path.stat().st_size // 1024
        logger.info("Saved %s (%d KB)", mp3_path.name, size_kb)
    else:
        logger.info("MP3 already exists for %s — skipping download.", call_id)

    # Extract contact metadata passed at call dispatch time
    metadata = call.get("metadata") or {}

    # Run transcription + formatting in a thread (AssemblyAI client is synchronous)
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _transcribe_and_format, mp3_path, call_id, metadata)

    return True


async def poll_and_download(batch_call_id: str) -> None:
    """
    Background task: poll Retell until all calls in the batch have ended,
    then for each completed call: download MP3 → transcribe → append to JSONL.
    """
    recordings_dir = Path(settings.recordings_dir)
    recordings_dir.mkdir(parents=True, exist_ok=True)

    processed: set[str] = set()
    max_polls = (MAX_WAIT_MINUTES * 60) // POLL_INTERVAL_SECONDS

    logger.info(
        "Recording poller started for batch %s. Checking every %ds, max wait %dmin.",
        batch_call_id, POLL_INTERVAL_SECONDS, MAX_WAIT_MINUTES,
    )

    async with httpx.AsyncClient() as client:
        for poll_num in range(1, int(max_polls) + 1):
            await asyncio.sleep(POLL_INTERVAL_SECONDS)

            try:
                calls = await _list_calls(client, batch_call_id)
            except Exception as exc:
                logger.warning("Poll %d failed: %s — will retry.", poll_num, exc)
                continue

            if not calls:
                logger.info("Poll %d: no calls found yet.", poll_num)
                continue

            total = len(calls)
            terminal = [c for c in calls if c.get("call_status") in TERMINAL_STATUSES]
            pending = total - len(terminal)

            logger.info(
                "Poll %d: %d/%d calls finished, %d still in progress.",
                poll_num, len(terminal), total, pending,
            )

            # Process any newly completed calls
            for call in terminal:
                call_id = call.get("call_id")
                if call_id not in processed:
                    await _process_call(client, call, recordings_dir)
                    processed.add(call_id)

            if pending == 0:
                logger.info(
                    "All %d calls complete. Processed %d recording(s).",
                    total, len(processed),
                )
                return

    logger.warning(
        "Poller timed out after %d minutes. Processed %d recording(s).",
        MAX_WAIT_MINUTES, len(processed),
    )
