from datetime import timedelta
from pathlib import Path

from liminal import (
    EvidenceGraph,
    Investigation,
    InvestigationWorkspace,
    ProvenanceEdge,
    SourceSnapshot,
    SnapshotStore,
    compare_text,
    content_hash,
    detect_gaps,
    semantic_hash,
    source_survival,
    utc_now,
)


def snapshot(url: str, text: str, observed_at):
    return SourceSnapshot(
        source_url=url,
        observed_at=observed_at,
        content=text,
        content_hash=content_hash(text),
        semantic_hash=semantic_hash(text),
        first_seen_at=observed_at,
        last_seen_at=observed_at,
    )


def test_hashing_distinguishes_bytes_from_semantics():
    assert content_hash("A  B") != content_hash("a b")
    assert semantic_hash("A  B") == semantic_hash("a b")


def test_semantic_diff_finds_quantitative_change():
    result = compare_text("The project had 12 users.", "The project had 19 users.")
    assert result.changed
    assert "quantitative" in result.classifications
    assert result.numeric_changes == ("12", "19")


def test_graph_tracks_copy_depth_and_origins():
    graph = EvidenceGraph()
    now = utc_now()
    graph.add_node("origin", "source")
    graph.add_node("copy", "source")
    graph.add_node("final", "source")
    graph.add_edge("e1", ProvenanceEdge("origin", "copy", "copies", now, 0.9))
    graph.add_edge("e2", ProvenanceEdge("copy", "final", "copies", now, 0.8))
    assert graph.propagation_depth("origin", "final", "copies") == 2
    assert graph.estimated_independent_origins("final") == 1


def test_archive_gaps_and_survival():
    start = utc_now() - timedelta(days=10)
    items = [
        snapshot("https://example.org", "one", start),
        snapshot("https://example.org", "two", start + timedelta(days=4)),
    ]
    gaps = detect_gaps(items)
    survival = source_survival(items)
    assert len(gaps) == 1
    assert gaps[0].missing_observations >= 1
    assert survival["https://example.org"]["semantic_versions"] == 2


def test_workspace_report_and_sqlite_store(tmp_path: Path):
    store_path = tmp_path / "liminal.db"
    investigation = Investigation("case_1", "Test Case")
    with SnapshotStore(store_path) as store:
        workspace = InvestigationWorkspace(investigation, store)
        now = utc_now()
        workspace.ingest_snapshot(
            snapshot(
                "https://example.org", "Liminal records a public claim about 2024.", now
            )
        )
        workspace.ingest_snapshot(
            snapshot(
                "https://example.org",
                "Liminal records a public claim about 2025.",
                now + timedelta(days=2),
            )
        )
        diff = workspace.compare_latest("https://example.org")
        assert diff is not None
        assert len(store.all_snapshots()) == 2
        assert "claim" in workspace.report_payload()["archival_relic"]
