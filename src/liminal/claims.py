from __future__ import annotations

import re
from datetime import datetime

from .hashing import content_hash, normalize_text
from .models import Claim, Entity


def _sentences(text: str) -> list[str]:
    cleaned = re.sub(r"\s+", " ", text).strip()
    return [item.strip() for item in re.split(r"(?<=[.!?])\s+", cleaned) if len(item.strip()) >= 20]


def extract_claims(text: str, source_url: str, observed_at: datetime, minimum_length: int = 20) -> list[Claim]:
    claims = []
    for sentence in _sentences(text):
        if len(sentence) < minimum_length:
            continue
        claim_id = "claim_" + content_hash(source_url + "|" + normalize_text(sentence))[:20]
        confidence = 0.6 if any(token in sentence.lower() for token in ("is", "are", "was", "were", "will", "announced", "reported")) else 0.4
        claims.append(Claim(claim_id=claim_id, text=sentence, source_url=source_url, observed_at=observed_at, confidence=confidence, quoted_text=sentence, evidence_hash=content_hash(sentence)))
    return claims


def extract_entities(text: str) -> list[Entity]:
    candidates = []
    candidates.extend(re.findall(r"\b[A-Z][A-Za-z0-9&.-]{2,}(?:\s+[A-Z][A-Za-z0-9&.-]{2,}){0,3}\b", text))
    candidates.extend(re.findall(r"\b(?:https?://|www\.)[^\s)]+", text))
    unique = []
    seen = set()
    for candidate in candidates:
        normalized = candidate.strip(".,;:()[]{}").strip()
        key = normalize_text(normalized)
        if len(key) < 3 or key in seen:
            continue
        seen.add(key)
        unique.append(normalized)
    entities = []
    for candidate in unique:
        entity_type = "domain" if candidate.startswith(("http://", "https://", "www.")) else "organization_or_concept"
        entity_id = "entity_" + content_hash(normalize_text(candidate))[:20]
        entities.append(Entity(entity_id=entity_id, canonical_name=candidate, entity_type=entity_type, aliases=(candidate,), confidence=0.45))
    return entities
