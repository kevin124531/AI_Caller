"""
Manually process an existing MP3 recording through the full pipeline:
  1. Transcribe with AssemblyAI (speaker diarization)
  2. Append training pairs to data/exports/training.jsonl

Usage:
    python scripts/process_recording.py --mp3 "data/recordings/call_abc123.mp3"

    # With contact metadata (improves the system prompt in the JSONL):
    python scripts/process_recording.py \
        --mp3 "data/recordings/call_abc123.mp3" \
        --job-title "VP of Data Center Engineering" \
        --specialisation "liquid cooling, high-density compute" \
        --category "Data Center Design & Operations"

    # Use a custom call ID (defaults to the MP3 filename without extension):
    python scripts/process_recording.py \
        --mp3 "path/to/recording.mp3" \
        --call-id "my_custom_id"
"""
import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from transcriber.audio_transcriber import transcribe_call
from formatter.qwen_formatter import append_to_jsonl

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s — %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(description="Process an MP3 recording into JSONL training data.")
    parser.add_argument("--mp3",           required=True, help="Path to the MP3 file")
    parser.add_argument("--call-id",       help="Call ID to use (defaults to MP3 filename)")
    parser.add_argument("--job-title",     default="digital infrastructure expert")
    parser.add_argument("--specialisation",default="data center operations")
    parser.add_argument("--category",      default="Data Center Design & Operations",
                        dest="question_category")
    args = parser.parse_args()

    mp3_path = Path(args.mp3)
    if not mp3_path.exists():
        logger.error("MP3 file not found: %s", mp3_path)
        sys.exit(1)

    call_id = args.call_id or mp3_path.stem
    metadata = {
        "job_title":         args.job_title,
        "specialisation":    args.specialisation,
        "question_category": args.question_category,
    }

    logger.info("Processing: %s", mp3_path)
    logger.info("Call ID:    %s", call_id)
    logger.info("Metadata:   %s", metadata)

    # Step 1 — Transcribe
    transcript_data = transcribe_call(mp3_path, call_id)
    speakers = transcript_data.get("speakers", {})
    logger.info("Speakers detected: %s", list(speakers.keys()))
    for speaker, utterances in speakers.items():
        word_count = sum(len(u["text"].split()) for u in utterances)
        logger.info("  %s — %d utterances, %d words", speaker, len(utterances), word_count)

    # Step 2 — Format and append to JSONL
    pairs = append_to_jsonl(transcript_data, metadata)

    if pairs:
        logger.info("Done. %d training pair(s) appended to data/exports/training.jsonl", pairs)
    else:
        logger.warning("No training pairs were extracted. Check the transcript in data/transcripts/%s/", call_id)


if __name__ == "__main__":
    main()
