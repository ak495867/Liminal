from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Iterable

from .models import SourceSnapshot


@dataclass(frozen=True)
class ArchiveGap:
    source_url: str
    start: datetime
    end: datetime
    missing_observations: int
    reason: str = "unobserved_interval"


def detect_gaps(snapshots: Iterable[SourceSnapshot], expected_interval: timedelta = timedelta(days=1), tolerance: float = 1.5) -> list[ArchiveGap]:
    grouped: dict[str, list[SourceSnapshot]] = {}
    for snapshot in snapshots:
        snapshot.validate()
        grouped.setdefault(snapshot.source_url, []).append(snapshot)
    gaps = []
    for source_url, items in grouped.items():
        ordered = sorted(items, key=lambda item: item.observed_at)
        for left, right in zip(ordered, ordered[1:]):
            elapsed = right.observed_at - left.observed_at
            threshold = expected_interval.total_seconds() * tolerance
            if elapsed.total_seconds() > threshold:
                missing = max(int(elapsed.total_seconds() // expected_interval.total_seconds()) - 1, 1)
                gaps.append(ArchiveGap(source_url, left.observed_at, right.observed_at, missing))
    return gaps


def source_survival(snapshots: Iterable[SourceSnapshot]) -> dict[str, dict[str, object]]:
    grouped: dict[str, list[SourceSnapshot]] = {}
    for snapshot in snapshots:
        grouped.setdefault(snapshot.source_url, []).append(snapshot)
    result = {}
    for source_url, items in grouped.items():
        ordered = sorted(items, key=lambda item: item.observed_at)
        first = ordered[0].observed_at
        last = ordered[-1].observed_at
        result[source_url] = {"first_seen": first.isoformat(), "last_seen": last.isoformat(), "observation_count": len(ordered), "active_days": max((last - first).days, 0), "semantic_versions": len({item.semantic_hash for item in ordered}), "content_versions": len({item.content_hash for item in ordered})}
    return result
