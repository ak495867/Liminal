from __future__ import annotations

import difflib
import re
from dataclasses import dataclass, asdict

from .hashing import normalize_text, similarity_ratio


@dataclass(frozen=True)
class SemanticDiff:
    changed: bool
    similarity: float
    added_tokens: tuple[str, ...]
    removed_tokens: tuple[str, ...]
    numeric_changes: tuple[str, ...]
    classifications: tuple[str, ...]
    summary: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _numbers(text: str) -> set[str]:
    return set(re.findall(r"(?<![A-Za-z])[-+]?\d+(?:[.,]\d+)?%?", text))


def _classify(left: str, right: str, added: set[str], removed: set[str], numbers_changed: bool) -> tuple[str, ...]:
    classes = []
    if numbers_changed:
        classes.append("quantitative")
    if added or removed:
        classes.append("claim_level")
    if len(left) < 120 or len(right) < 120:
        classes.append("metadata")
    if not classes and left != right:
        classes.append("cosmetic_or_formatting")
    return tuple(dict.fromkeys(classes))


def compare_text(left: str, right: str) -> SemanticDiff:
    left_normalized = normalize_text(left)
    right_normalized = normalize_text(right)
    left_tokens = left_normalized.split()
    right_tokens = right_normalized.split()
    matcher = difflib.SequenceMatcher(a=left_tokens, b=right_tokens, autojunk=False)
    added = set(right_tokens).difference(left_tokens)
    removed = set(left_tokens).difference(right_tokens)
    numeric_changes = _numbers(left).symmetric_difference(_numbers(right))
    classifications = _classify(left_normalized, right_normalized, added, removed, bool(numeric_changes))
    similarity = similarity_ratio(left, right)
    changed = left_normalized != right_normalized
    if not changed:
        summary = "No semantic change detected. The page stayed in the same liminal state."
    elif matcher.ratio() > 0.98:
        summary = "Minor textual change detected."
    else:
        summary = "Material textual change detected across the evidence surface."
    return SemanticDiff(changed, similarity, tuple(sorted(added)), tuple(sorted(removed)), tuple(sorted(numeric_changes)), classifications, summary)
