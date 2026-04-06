"""
Auto-scorer v1: rule-based scoring using VADER sentiment + question completion heuristics.
Each dimension returns a float in [0.0, 1.0].
"""
import re
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

_analyzer = SentimentIntensityAnalyzer()

# Questions the agent is expected to ask (keywords to detect in agent turns)
EXPECTED_QUESTION_KEYWORDS = [
    r"scale from 1 to 10",
    r"overall experience",
    r"frustrated|could have been better",
    r"change one thing",
    r"likely.*recommend",
]

SCORER_VERSION = "v1"


def score_transcript(segments: list[dict]) -> dict[str, float]:
    agent_turns = [s["content"] for s in segments if s["role"] == "agent"]
    user_turns = [s["content"] for s in segments if s["role"] == "user"]

    return {
        "sentiment": _sentiment_score(user_turns),
        "completion_rate": _completion_rate(agent_turns),
        "avg_response_length": _avg_response_length(user_turns),
        "user_turn_count": float(len(user_turns)),
    }


def _sentiment_score(user_turns: list[str]) -> float:
    if not user_turns:
        return 0.5
    scores = [_analyzer.polarity_scores(t)["compound"] for t in user_turns]
    avg = sum(scores) / len(scores)
    return (avg + 1) / 2  # normalise [-1,1] -> [0,1]


def _completion_rate(agent_turns: list[str]) -> float:
    if not agent_turns:
        return 0.0
    full_text = " ".join(agent_turns).lower()
    matched = sum(
        1 for pattern in EXPECTED_QUESTION_KEYWORDS if re.search(pattern, full_text)
    )
    return matched / len(EXPECTED_QUESTION_KEYWORDS)


def _avg_response_length(user_turns: list[str]) -> float:
    if not user_turns:
        return 0.0
    avg_words = sum(len(t.split()) for t in user_turns) / len(user_turns)
    return min(avg_words / 50.0, 1.0)  # normalise: 50 words = 1.0
