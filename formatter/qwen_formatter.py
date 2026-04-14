"""
Converts a call transcript into ChatML training examples and appends them
to data/exports/training.jsonl.

Speaker identification:
  The speaker with the most total words is treated as the expert (assistant).
  The other speaker is the interviewer (user).

System prompt:
  Built from contact metadata — role-based, not name-based.
  e.g. "You are a VP of Infrastructure specialising in liquid cooling..."
"""

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

JSONL_PATH = Path("data/exports/training.jsonl")
MIN_RESPONSE_LEN = 50  # minimum characters for an expert utterance to be included

SYSTEM_PROMPT_TEMPLATE = (
    "You are a {job_title} specialising in {specialisation}. "
    "You are an experienced member of iMasons with deep expertise in {question_category}. "
    "You provide detailed, experience-based insights on digital infrastructure topics, "
    "drawing from real-world practice and lessons learned in the field."
)


def _identify_expert_speaker(speakers: dict) -> str:
    """
    Return the speaker label with the most total words.
    In a survey call the expert gives longer answers than the interviewer.
    """
    return max(
        speakers.keys(),
        key=lambda s: sum(len(u["text"].split()) for u in speakers[s]),
    )


def _build_qa_pairs(transcript_data: dict) -> list[dict]:
    """
    Walk the utterances and build (user, assistant) pairs.

    For each expert utterance long enough to be a real answer, collect up to
    3 preceding interviewer utterances as the user turn.
    """
    utterances = transcript_data.get("utterances", [])
    speakers = transcript_data.get("speakers", {})

    if not utterances or not speakers:
        return []

    expert_speaker = _identify_expert_speaker(speakers)
    pairs = []

    for i, u in enumerate(utterances):
        if u["speaker"] != expert_speaker:
            continue
        if len(u["text"]) < MIN_RESPONSE_LEN:
            continue

        # Collect preceding interviewer turns (same conversation, stop at another expert turn)
        context_parts = []
        for j in range(i - 1, max(0, i - 4), -1):
            prev = utterances[j]
            if prev["speaker"] == expert_speaker:
                break
            context_parts.insert(0, prev["text"].strip())

        if not context_parts:
            continue

        pairs.append({
            "user": " ".join(context_parts),
            "assistant": u["text"].strip(),
        })

    return pairs


def _build_system_prompt(metadata: dict) -> str:
    return SYSTEM_PROMPT_TEMPLATE.format(
        job_title=metadata.get("job_title", "digital infrastructure expert"),
        specialisation=metadata.get("specialisation", "data center operations"),
        question_category=metadata.get("question_category", "digital infrastructure"),
    )


def append_to_jsonl(transcript_data: dict, metadata: dict) -> int:
    """
    Convert a transcript into ChatML training examples and append to training.jsonl.

    Args:
        transcript_data:  Dict returned by transcriber.transcribe_call().
        metadata:         Contact metadata dict with keys:
                            job_title, specialisation, question_category.

    Returns:
        Number of training pairs appended.
    """
    JSONL_PATH.parent.mkdir(parents=True, exist_ok=True)

    pairs = _build_qa_pairs(transcript_data)
    if not pairs:
        logger.warning(
            "No Q&A pairs extracted from call %s — nothing appended.",
            transcript_data.get("call_id"),
        )
        return 0

    system_prompt = _build_system_prompt(metadata)
    call_id = transcript_data.get("call_id", "unknown")

    with open(JSONL_PATH, "a", encoding="utf-8") as f:
        for pair in pairs:
            example = {
                "messages": [
                    {"role": "system",    "content": system_prompt},
                    {"role": "user",      "content": pair["user"]},
                    {"role": "assistant", "content": pair["assistant"]},
                ],
                "metadata": {
                    "call_id": call_id,
                    "source": "ai_caller",
                    "job_title":          metadata.get("job_title"),
                    "specialisation":     metadata.get("specialisation"),
                    "question_category":  metadata.get("question_category"),
                },
            }
            f.write(json.dumps(example, ensure_ascii=False) + "\n")

    logger.info(
        "Appended %d training pair(s) from call %s to %s",
        len(pairs), call_id, JSONL_PATH,
    )
    return len(pairs)
