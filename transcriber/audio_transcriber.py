"""
Transcribes a call MP3 using AssemblyAI with speaker diarization.

Saves the following files to data/transcripts/<call_id>/:
  full_transcript.txt       — plain text, no speaker labels
  conversation.txt          — labelled turn-by-turn conversation
  speaker_a_transcript.txt  — all utterances from Speaker A
  speaker_b_transcript.txt  — all utterances from Speaker B
  transcript_data.json      — full structured data (used by formatter)
"""

import json
import logging
from pathlib import Path

import assemblyai as aai

from config.settings import settings

logger = logging.getLogger(__name__)


def transcribe_call(mp3_path: Path, call_id: str) -> dict:
    """
    Transcribe a call recording with speaker diarization.

    Args:
        mp3_path:  Path to the downloaded MP3 file.
        call_id:   Retell call_id — used as the output subdirectory name.

    Returns:
        Transcript data dict (same structure saved to transcript_data.json).
    """
    output_dir = Path(settings.transcripts_dir) / call_id
    output_dir.mkdir(parents=True, exist_ok=True)

    json_path = output_dir / "transcript_data.json"
    if json_path.exists():
        logger.info("Transcript already exists for %s — loading from disk.", call_id)
        return json.loads(json_path.read_text(encoding="utf-8"))

    aai.settings.api_key = settings.assemblyai_api_key

    config = aai.TranscriptionConfig(
        speaker_labels=True,
        speakers_expected=2,
        speech_models=["universal-3-pro"],
    )

    logger.info("Uploading %s to AssemblyAI for transcription...", mp3_path.name)
    transcriber = aai.Transcriber()
    transcript = transcriber.transcribe(str(mp3_path), config=config)

    if transcript.status == aai.TranscriptStatus.error:
        raise RuntimeError(f"AssemblyAI transcription failed for {call_id}: {transcript.error}")

    # Organise utterances by speaker
    speaker_transcripts: dict[str, list] = {}
    for utterance in transcript.utterances:
        label = f"Speaker {utterance.speaker}"
        speaker_transcripts.setdefault(label, []).append({
            "text": utterance.text,
            "start": utterance.start,
            "end": utterance.end,
            "confidence": utterance.confidence,
        })

    result = {
        "call_id": call_id,
        "full_transcript": transcript.text,
        "speakers": speaker_transcripts,
        "utterances": [
            {
                "speaker": f"Speaker {u.speaker}",
                "text": u.text,
                "start": u.start,
                "end": u.end,
            }
            for u in transcript.utterances
        ],
    }

    _save_transcript_files(result, output_dir)
    logger.info("Transcript saved to %s", output_dir)
    return result


def _save_transcript_files(result: dict, output_dir: Path) -> None:
    """Write all transcript text files and the master JSON."""
    # Plain text
    (output_dir / "full_transcript.txt").write_text(
        result["full_transcript"] or "", encoding="utf-8"
    )

    # Labelled conversation
    conversation = "\n\n".join(
        f"[{u['speaker']}]: {u['text']}" for u in result["utterances"]
    )
    (output_dir / "conversation.txt").write_text(conversation, encoding="utf-8")

    # Per-speaker files
    for speaker, utterances in result["speakers"].items():
        fname = f"{speaker.lower().replace(' ', '_')}_transcript.txt"
        text = "\n\n".join(u["text"] for u in utterances)
        (output_dir / fname).write_text(text, encoding="utf-8")

    # Master JSON
    (output_dir / "transcript_data.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8"
    )
