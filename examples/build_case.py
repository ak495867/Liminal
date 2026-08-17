from datetime import timedelta

from liminal import Investigation, InvestigationWorkspace, SourceSnapshot, content_hash, semantic_hash, utc_now


investigation = Investigation("example_case", "The Page That Changed Its Story")
workspace = InvestigationWorkspace(investigation)
first = utc_now() - timedelta(days=4)
second = utc_now() - timedelta(days=2)
for observed_at, content in (
    (first, "The archive project launched in 2024 and preserves public source changes."),
    (second, "The archive project launched in 2025 and preserves public source changes with uncertainty labels."),
):
    workspace.ingest_snapshot(SourceSnapshot(source_url="https://example.org/archive", observed_at=observed_at, content=content, content_hash=content_hash(content), semantic_hash=semantic_hash(content), title="Archive page", source_type="fixture", first_seen_at=first, last_seen_at=observed_at))
workspace.compare_latest("https://example.org/archive")
print(workspace.report_payload()["archival_relic"])
