from __future__ import annotations

import argparse
import json
from datetime import timedelta
from pathlib import Path

from .collectors import FetchPolicy, fetch_url
from .hashing import content_hash, semantic_hash
from .investigation import InvestigationWorkspace
from .models import Investigation, SourceSnapshot, utc_now
from .reporting import write_reports
from .semantic_diff import compare_text
from .storage import SnapshotStore


def _demo_workspace() -> InvestigationWorkspace:
    investigation = Investigation(investigation_id="demo_liminal", title="A Small Archaeology of a Changing Public Claim")
    workspace = InvestigationWorkspace(investigation)
    first_time = utc_now() - timedelta(days=3)
    second_time = utc_now() - timedelta(days=1)
    first_content = "Liminal Research announced a public archive project in 2024. The project preserves public evidence and records source changes."
    second_content = "Liminal Research announced a public archive project in 2025. The project preserves public evidence, records source changes, and publishes uncertainty notes."
    for observed_at, content in ((first_time, first_content), (second_time, second_content)):
        workspace.ingest_snapshot(SourceSnapshot(source_url="https://example.org/liminal", observed_at=observed_at, content=content, content_hash=content_hash(content), semantic_hash=semantic_hash(content), title="Liminal Research Archive", source_type="fixture", first_seen_at=first_time, last_seen_at=observed_at))
    workspace.compare_latest("https://example.org/liminal")
    if len(workspace.claims) >= 2:
        workspace.link_copy(workspace.claims[0].claim_id, workspace.claims[-1].claim_id, second_time, 0.7)
    workspace.investigation.add_note("A copied claim walks into a graph and meets its original source.")
    return workspace


def demo_main(args: argparse.Namespace) -> None:
    workspace = _demo_workspace()
    paths = write_reports(workspace, args.output)
    print(json.dumps({"output": {name: str(path) for name, path in paths.items()}, "relic": "The web is not dead; it is merely in a different archive."}, indent=2))


def diff_main(args: argparse.Namespace) -> None:
    left = Path(args.left).read_text(encoding="utf-8")
    right = Path(args.right).read_text(encoding="utf-8")
    print(json.dumps(compare_text(left, right).to_dict(), indent=2))


def hash_main(args: argparse.Namespace) -> None:
    content = Path(args.path).read_text(encoding="utf-8")
    print(json.dumps({"content_hash": content_hash(content), "semantic_hash": semantic_hash(content), "relic": "Temporal OSINT: because yesterday deserves a diff."}, indent=2))


def collect_main(args: argparse.Namespace) -> None:
    snapshot = fetch_url(args.url, FetchPolicy(timeout_seconds=args.timeout, maximum_bytes=args.maximum_bytes))
    with SnapshotStore(args.database) as store:
        row_id = store.save_snapshot(snapshot)
    print(json.dumps({"snapshot_row_id": row_id, "source_url": snapshot.source_url, "observed_at": snapshot.observed_at.isoformat(), "content_hash": snapshot.content_hash, "semantic_hash": snapshot.semantic_hash, "relic": "The collector knocked politely; the archive answered with a hash."}, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(prog="liminal")
    subparsers = parser.add_subparsers(dest="command", required=True)
    demo = subparsers.add_parser("demo")
    demo.add_argument("--output", default="reports/demo")
    demo.set_defaults(handler=demo_main)
    diff = subparsers.add_parser("diff")
    diff.add_argument("left")
    diff.add_argument("right")
    diff.set_defaults(handler=diff_main)
    hash_parser = subparsers.add_parser("hash")
    hash_parser.add_argument("path")
    hash_parser.set_defaults(handler=hash_main)
    collect = subparsers.add_parser("collect")
    collect.add_argument("url")
    collect.add_argument("--database", default="liminal.db")
    collect.add_argument("--timeout", type=float, default=15.0)
    collect.add_argument("--maximum-bytes", type=int, default=5_000_000)
    collect.set_defaults(handler=collect_main)
    args = parser.parse_args()
    args.handler(args)


if __name__ == "__main__":
    main()
