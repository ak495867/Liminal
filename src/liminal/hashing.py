from __future__ import annotations

import hashlib
import re
import unicodedata


def normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKC", text)
    normalized = normalized.replace("\r\n", "\n").replace("\r", "\n")
    normalized = re.sub(r"\s+", " ", normalized).strip().lower()
    return normalized


def content_hash(content: str | bytes, algorithm: str = "sha256") -> str:
    value = content.encode("utf-8") if isinstance(content, str) else content
    try:
        digest = hashlib.new(algorithm)
    except ValueError as exc:
        raise ValueError(f"unsupported hash algorithm: {algorithm}") from exc
    digest.update(value)
    return digest.hexdigest()


def semantic_hash(content: str, algorithm: str = "sha256") -> str:
    return content_hash(normalize_text(content), algorithm)


def similarity_ratio(left: str, right: str) -> float:
    left_tokens = normalize_text(left).split()
    right_tokens = normalize_text(right).split()
    if not left_tokens and not right_tokens:
        return 1.0
    if not left_tokens or not right_tokens:
        return 0.0
    left_counts = {}
    right_counts = {}
    for token in left_tokens:
        left_counts[token] = left_counts.get(token, 0) + 1
    for token in right_tokens:
        right_counts[token] = right_counts.get(token, 0) + 1
    overlap = sum(min(left_counts.get(token, 0), count) for token, count in right_counts.items())
    return float(2.0 * overlap / (len(left_tokens) + len(right_tokens)))
