"""Content analytics helpers."""

from __future__ import annotations

import re
from collections import Counter
from datetime import datetime
from typing import Iterable, List, Optional

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from .models import ContentAnalytics, KeywordScore, PostContent, PostSummary, SentimentBreakdown


_TOKEN_RE = re.compile(r"[A-Za-z']+")
_SENTENCE_RE = re.compile(r"[^.!?]+")
_VOWELS = "aeiouy"
_STOPWORDS = {
    "a",
    "about",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "but",
    "by",
    "for",
    "from",
    "has",
    "have",
    "he",
    "in",
    "is",
    "it",
    "its",
    "of",
    "on",
    "or",
    "she",
    "that",
    "the",
    "their",
    "there",
    "to",
    "was",
    "were",
    "will",
    "with",
    "you",
    "your",
}
_ANALYSER = SentimentIntensityAnalyzer()


def _tokenise(text: str) -> List[str]:
    return [match.group(0).lower() for match in _TOKEN_RE.finditer(text)]


def _sentence_lengths(text: str) -> List[int]:
    return [len(_TOKEN_RE.findall(sentence)) for sentence in _SENTENCE_RE.findall(text) if sentence.strip()]


def _count_syllables(word: str) -> int:
    word = word.lower()
    syllables = 0
    previous_char_was_vowel = False
    for char in word:
        if char in _VOWELS:
            if not previous_char_was_vowel:
                syllables += 1
                previous_char_was_vowel = True
        else:
            previous_char_was_vowel = False
    if word.endswith("e") and syllables > 1:
        syllables -= 1
    return syllables or 1


def _flesch_reading_ease(word_count: int, sentence_count: int, syllable_count: int) -> float:
    if word_count == 0 or sentence_count == 0:
        return 0.0
    words_per_sentence = word_count / sentence_count
    syllables_per_word = syllable_count / word_count
    return 206.835 - (1.015 * words_per_sentence) - (84.6 * syllables_per_word)


def _flesch_kincaid_grade(word_count: int, sentence_count: int, syllable_count: int) -> float:
    if word_count == 0 or sentence_count == 0:
        return 0.0
    words_per_sentence = word_count / sentence_count
    syllables_per_word = syllable_count / word_count
    return (0.39 * words_per_sentence) + (11.8 * syllables_per_word) - 15.59


def _keywords(tokens: Iterable[str], top_n: int = 12) -> List[KeywordScore]:
    counter = Counter(token for token in tokens if token not in _STOPWORDS and len(token) > 2)
    if not counter:
        return []
    total = sum(counter.values())
    most_common = counter.most_common(top_n)
    return [KeywordScore(term=term, score=count / total) for term, count in most_common]


def _publishing_cadence_days(history: List[PostSummary]) -> Optional[float]:
    timestamps = [summary.published_at for summary in history if summary.published_at]
    timestamps = sorted(timestamps, reverse=True)
    if len(timestamps) < 2:
        return None
    deltas = [
        (timestamps[idx] - timestamps[idx + 1]).total_seconds() / 86400
        for idx in range(len(timestamps) - 1)
    ]
    if not deltas:
        return None
    return sum(deltas) / len(deltas)


def analyse_post(content: PostContent, history: Optional[List[PostSummary]] = None) -> ContentAnalytics:
    """Run keyword, sentiment, and readability analytics for a post."""

    text = content.text or ""
    tokens = _tokenise(text)
    word_count = len(tokens)
    sentence_lengths = _sentence_lengths(text)
    sentence_count = len(sentence_lengths) or 1
    syllable_count = sum(_count_syllables(token) for token in tokens)

    sentiment = None
    if text.strip():
        scores = _ANALYSER.polarity_scores(text)
        sentiment = SentimentBreakdown(
            negative=scores["neg"],
            neutral=scores["neu"],
            positive=scores["pos"],
            compound=scores["compound"],
        )

    keywords = _keywords(tokens)

    lexical_diversity = (len(set(tokens)) / word_count) if word_count else None
    avg_sentence_length = (sum(sentence_lengths) / len(sentence_lengths)) if sentence_lengths else None

    flesch = _flesch_reading_ease(word_count, sentence_count, syllable_count)
    fk_grade = _flesch_kincaid_grade(word_count, sentence_count, syllable_count)

    cadence_days = _publishing_cadence_days(history or [])

    return ContentAnalytics(
        summary=content.summary,
        sentiment=sentiment,
        keywords=keywords,
        flesch_reading_ease=flesch,
        flesch_kincaid_grade=fk_grade,
        lexical_diversity=lexical_diversity,
        average_sentence_length=avg_sentence_length,
        publishing_cadence_days=cadence_days,
        extra={
            "word_count": word_count,
            "sentence_count": sentence_count,
            "syllable_count": syllable_count,
            "generated_at": datetime.utcnow().isoformat(),
        },
    )

