from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any



def utc_now() -> datetime:
    return datetime.now(timezone.utc)



@dataclass(frozen=True)
class SourceSnapshot:
    source_url: str
    observed_at: datetime
    content: str
    content_hash: str
    semantic_hash: str
    source_type: str = "web"
    published_at: datetime | None = None
    title: str | None = None
    status_code: int | None = None
    content_type: str | None = None
    first_seen_at: datetime | None = None
    last_seen_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.source_url.startswith(("http://", "https://")):
            raise ValueError("source_url must use http or https")
        if not self.content_hash or not self.semantic_hash:
            raise ValueError("snapshot hashes must not be empty")
        if self.status_code is not None and not 100 <= self.status_code <= 599:
            raise ValueError("status_code must be an HTTP status code")


@dataclass(frozen=True)
class Claim:
    claim_id: str
    text: str
    source_url: str
    observed_at: datetime
    confidence: float = 0.5
    subject: str | None = None
    predicate: str | None = None
    object_value: str | None = None
    quoted_text: str | None = None
    evidence_hash: str | None = None

    def validate(self) -> None:
        if not self.claim_id or not self.text or not self.source_url:
            raise ValueError("claim_id, text, and source_url are required")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be in [0, 1]")


@dataclass(frozen=True)
class Entity:
    entity_id: str
    canonical_name: str
    entity_type: str
    aliases: tuple[str, ...] = field(default_factory=tuple)
    attributes: dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.5

    def validate(self) -> None:
        if not self.entity_id or not self.canonical_name or not self.entity_type:
            raise ValueError("entity_id, canonical_name, and entity_type are required")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be in [0, 1]")


@dataclass(frozen=True)
class ProvenanceEdge:
    source_id: str
    target_id: str
    relation: str
    observed_at: datetime
    confidence: float = 0.5
    evidence_url: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.source_id or not self.target_id or not self.relation:
            raise ValueError("source_id, target_id, and relation are required")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be in [0, 1]")


@dataclass
class Investigation:
    investigation_id: str
    title: str
    created_at: datetime = field(default_factory=utc_now)
    analyst: str = "ak495867"
    scope: str = "public information"
    snapshot_ids: list[str] = field(default_factory=list)
    claim_ids: list[str] = field(default_factory=list)
    entity_ids: list[str] = field(default_factory=list)
    edge_ids: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def add_note(self, note: str) -> None:
        if note.strip():
            self.notes.append(note.strip())

    def validate(self) -> None:
        if not self.investigation_id or not self.title:
            raise ValueError("investigation_id and title are required")
        if not self.scope:
            raise ValueError("scope must not be empty")
