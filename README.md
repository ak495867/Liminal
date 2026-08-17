# Liminal: Temporal Internet Evidence Graph

Liminal reconstructs how public claims, organizations, documents, websites, and digital infrastructure change over time. It treats the public internet as a time-varying evidence system rather than a collection of current pages.

> The present is only one version of the evidence.

## What Liminal studies

Liminal is designed for passive, reproducible, public-source research. It records observations, preserves content and semantic hashes, compares versions, extracts claims and entities, tracks provenance, estimates narrative propagation, detects archive gaps, and produces investigation reports.

The central research question is:

> How can an investigator distinguish independent corroboration from copied narratives, silent edits, archival gaps, and changing source definitions?

Liminal does not infer intent, guilt, ownership, or truth solely from repetition, deletion, timing, or association. It preserves uncertainty and expects human review.

## Capabilities

| Capability | Description |
| --- | --- |
| Temporal snapshots | Store observed time, optional publication time, content, hashes, title, status, and metadata |
| Semantic diffs | Separate meaningful text changes from byte-level or formatting changes |
| Claim extraction | Create stable claim IDs from normalized source text and provenance |
| Entity extraction | Detect public domains and capitalized organization or concept candidates |
| Evidence graph | Connect sources, snapshots, claims, entities, citations, and copies |
| Propagation analysis | Estimate graph depth and possible independent origins |
| Archive gaps | Detect missing observation intervals under an expected schedule |
| Local persistence | Store evidence in SQLite with deterministic JSON-ready exports |
| Passive collectors | Fetch public HTTP, HTTPS, and RSS content with bounded downloads |
| Reports | Generate Markdown and JSON investigation reports |
| Reproducibility | Use content hashes, semantic hashes, explicit timestamps, and local fixtures |

## The temporal model

Liminal distinguishes the event time, publication time, observation time, and archival time of information. A source can be published at one time, observed later, revised without changing its URL, and archived at a different time.

Each snapshot carries:

```text
source_url
observed_at
published_at
content_hash
semantic_hash
source_type
title
status_code
content_type
metadata
```

The byte-level content hash answers whether downloaded bytes changed. The semantic hash answers whether normalized visible text changed. Neither hash establishes truth.

## Installation

Use Python 3.10 or newer.

```text
python -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

## CLI

Run the local demo:

```text
liminal demo --output reports/demo
```

The demo writes `investigation.md` and `investigation.json` and includes two changing public-source snapshots, a semantic diff, claims, entities, graph edges, and an archive-gap calculation.

Compare two local text files:

```text
liminal diff before.txt after.txt
```

Hash a local evidence file:

```text
liminal hash source.txt
```

Collect one public URL passively into SQLite:

```text
liminal collect https://example.org --database data/liminal.db
```

The collector does not authenticate, submit forms, probe paths, bypass access controls, or target private and loopback addresses. Respect source terms, rate limits, robots directives, and applicable law.

## Python example

```python
from datetime import timedelta

from liminal import Investigation, InvestigationWorkspace, SourceSnapshot, content_hash, semantic_hash, utc_now

investigation = Investigation("case_001", "A Changing Public Claim")
workspace = InvestigationWorkspace(investigation)
observed_at = utc_now()
content = "A public source published a claim about a project in 2024."
snapshot = SourceSnapshot(source_url="https://example.org/source", observed_at=observed_at, content=content, content_hash=content_hash(content), semantic_hash=semantic_hash(content), title="Example source", first_seen_at=observed_at, last_seen_at=observed_at)
workspace.ingest_snapshot(snapshot)
print(workspace.report_payload())
```

## Project relics

Liminal contains no comment-based narration in executable source. Small project jokes appear as contextual runtime relics near the concept they belong to: a semantic diff, a collector response, an investigation report, a demo fixture, or a test assertion. They are not collected into one registry, because even jokes deserve provenance.

## Repository structure

| Path | Purpose |
| --- | --- |
| `src/liminal/models.py` | Evidence, claim, entity, provenance, and investigation models |
| `src/liminal/hashing.py` | Content, semantic, and similarity functions |
| `src/liminal/storage.py` | SQLite snapshot and graph persistence |
| `src/liminal/semantic_diff.py` | Semantic change classification |
| `src/liminal/claims.py` | Deterministic claims and entities |
| `src/liminal/graph.py` | Provenance and propagation graph |
| `src/liminal/gaps.py` | Archive gaps and source survival metrics |
| `src/liminal/investigation.py` | Reproducible investigation workspace |
| `src/liminal/collectors/` | Passive public web and RSS collectors |
| `src/liminal/reporting.py` | Markdown and JSON report generation |
| `schemas/` | JSON Schema contracts |
| `tests/` | Temporal, semantic, graph, storage, and safety tests |

## Testing

```text
pytest
```

The test suite checks hash semantics, quantitative diff detection, graph propagation depth, root-origin estimation, archive gaps, source survival, SQLite persistence, report payloads, and safe collector URL validation.

## Safety boundary

Liminal is for passive, public, and authorized OSINT. It should be used for public-source collection, archival comparison, provenance tracking, defensive domain monitoring, open-source project analysis, change detection, and evidence-quality reporting.

It must not be extended for credential theft, unauthorized access, exploitation, persistence, evasion, doxxing, stalking, or targeting private individuals. Any future connector must preserve the passive and authorized boundary.

## License

MIT License under `ak495867`. See `LICENSE`.
