from webhook.models import CallObject, TranscriptUtterance


def parse_transcript(call: CallObject) -> list[dict]:
    """Extract utterances from a Retell call object into a normalised segment list."""
    utterances: list[TranscriptUtterance] = call.transcript_object or []
    segments = []
    for utt in utterances:
        words = utt.words or []
        start_ms = int(words[0].get("start", 0) * 1000) if words else None
        end_ms = int(words[-1].get("end", 0) * 1000) if words else None
        segments.append(
            {
                "role": utt.role,
                "content": utt.content,
                "start_ms": start_ms,
                "end_ms": end_ms,
            }
        )
    return segments
