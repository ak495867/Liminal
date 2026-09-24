from __future__ import annotations

import ipaddress
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from html.parser import HTMLParser
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from ..hashing import content_hash, semantic_hash
from ..models import SourceSnapshot


@dataclass(frozen=True)
class FetchPolicy:
    timeout_seconds: float = 15.0
    maximum_bytes: int = 5_000_000
    user_agent: str = "Liminal/0.1 (+public-research; passive-collection)"


class _TextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.title_parts: list[str] = []
        self.text_parts: list[str] = []
        self.in_title = False
        self.skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "title":
            self.in_title = True
        if tag.lower() in {"script", "style", "noscript", "svg"}:
            self.skip_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "title":
            self.in_title = False
        if tag.lower() in {"script", "style", "noscript", "svg"} and self.skip_depth:
            self.skip_depth -= 1

    def handle_data(self, data: str) -> None:
        if self.skip_depth:
            return
        if self.in_title:
            self.title_parts.append(data)
        self.text_parts.append(data)

    @property
    def title(self) -> str | None:
        value = re.sub(r"\s+", " ", " ".join(self.title_parts)).strip()
        return value or None

    @property
    def text(self) -> str:
        return re.sub(r"\s+", " ", " ".join(self.text_parts)).strip()


def _validate_public_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("only public http and https URLs are supported")
    hostname = parsed.hostname.lower()
    if hostname in {"localhost", "localhost.localdomain"} or hostname.endswith(
        ".local"
    ):
        raise ValueError("local hostnames are not supported")
    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        return
    if (
        address.is_private
        or address.is_loopback
        or address.is_link_local
        or address.is_reserved
    ):
        raise ValueError(
            "private, loopback, link-local, and reserved addresses are not supported"
        )


def fetch_url(
    url: str, policy: FetchPolicy = FetchPolicy(), observed_at: datetime | None = None
) -> SourceSnapshot:
    _validate_public_url(url)
    request = Request(
        url,
        headers={
            "User-Agent": policy.user_agent,
            "Accept": "text/html, text/plain, application/xhtml+xml, application/xml;q=0.9",
        },
    )
    with urlopen(request, timeout=policy.timeout_seconds) as response:
        body = response.read(policy.maximum_bytes + 1)
        if len(body) > policy.maximum_bytes:
            raise ValueError("response exceeds maximum_bytes")
        content_type = response.headers.get("Content-Type")
        status_code = getattr(response, "status", None)
        final_url = response.geturl()
    decoded = body.decode("utf-8", errors="replace")
    parser = _TextParser()
    parser.feed(decoded)
    text = parser.text or decoded
    timestamp = observed_at or datetime.now(timezone.utc)
    snapshot = SourceSnapshot(
        source_url=final_url,
        observed_at=timestamp,
        content=text,
        content_hash=content_hash(decoded),
        semantic_hash=semantic_hash(text),
        source_type="web",
        title=parser.title,
        status_code=status_code,
        content_type=content_type,
        first_seen_at=timestamp,
        last_seen_at=timestamp,
        metadata={"requested_url": url, "collector": "passive_web"},
    )
    snapshot.validate()
    return snapshot
