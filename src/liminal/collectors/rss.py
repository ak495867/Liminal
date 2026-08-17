from __future__ import annotations

import email.utils
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from urllib.request import Request, urlopen

from ..hashing import content_hash, semantic_hash
from ..models import SourceSnapshot
from .web import FetchPolicy, _validate_public_url


def _parse_date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = email.utils.parsedate_to_datetime(value)
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except (TypeError, ValueError, OverflowError):
        return None


def fetch_rss(url: str, policy: FetchPolicy = FetchPolicy(), observed_at: datetime | None = None) -> list[SourceSnapshot]:
    _validate_public_url(url)
    request = Request(url, headers={"User-Agent": policy.user_agent, "Accept": "application/rss+xml, application/atom+xml, application/xml;q=0.9"})
    with urlopen(request, timeout=policy.timeout_seconds) as response:
        body = response.read(policy.maximum_bytes + 1)
    if len(body) > policy.maximum_bytes:
        raise ValueError("response exceeds maximum_bytes")
    root = ET.fromstring(body)
    timestamp = observed_at or datetime.now(timezone.utc)
    snapshots = []
    for item in root.findall(".//item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or url).strip()
        description = (item.findtext("description") or "").strip()
        published = _parse_date(item.findtext("pubDate"))
        content = " ".join(value for value in (title, description) if value)
        snapshots.append(SourceSnapshot(source_url=link, observed_at=timestamp, published_at=published, content=content, content_hash=content_hash(content), semantic_hash=semantic_hash(content), source_type="rss", title=title or None, first_seen_at=timestamp, last_seen_at=timestamp, metadata={"feed_url": url, "collector": "passive_rss"}))
    return snapshots
