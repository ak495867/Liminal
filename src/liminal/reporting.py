from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .investigation import InvestigationWorkspace


def build_markdown_report(workspace: InvestigationWorkspace) -> str:
    payload = workspace.report_payload()
    investigation = payload["investigation"]
    lines = [
        f"# Liminal Investigation: {investigation['title']}",
        "",
        "> This report is based on passive public-source observations and preserves uncertainty rather than manufacturing certainty.",
        "",
        "## Case metadata",
        "",
        f"- Investigation ID: `{investigation['investigation_id']}`",
        f"- Analyst: `{investigation['analyst']}`",
        f"- Scope: {investigation['scope']}",
        f"- Snapshots: {payload['snapshot_count']}",
        f"- Claims: {payload['claim_count']}",
        f"- Entities: {payload['entity_count']}",
        f"- Semantic diffs: {payload['diff_count']}",
        "",
        "## Source timeline",
        "",
    ]
    for snapshot in sorted(workspace.snapshots, key=lambda item: item.observed_at):
        lines.append(
            f"- `{snapshot.observed_at.isoformat()}` — [{snapshot.title or snapshot.source_url}]({snapshot.source_url}) — semantic hash `{snapshot.semantic_hash[:16]}`"
        )
    if not workspace.snapshots:
        lines.append("No snapshots were ingested.")
    lines.extend(["", "## Semantic changes", ""])
    if workspace.diffs:
        for index, diff in enumerate(workspace.diffs, start=1):
            lines.append(
                f"{index}. **{diff.summary}** Similarity `{diff.similarity:.3f}`. Classes: `{', '.join(diff.classifications) or 'none'}`."
            )
            if diff.numeric_changes:
                lines.append(f"   Numeric changes: `{', '.join(diff.numeric_changes)}`")
    else:
        lines.append("No pairwise semantic diff has been recorded.")
    lines.extend(["", "## Archive gaps", ""])
    gaps = payload["archive_gaps"]
    if gaps:
        for gap in gaps:
            lines.append(
                f"- `{gap['source_url']}` from `{gap['start']}` to `{gap['end']}` with at least `{gap['missing_observations']}` missing observations."
            )
    else:
        lines.append(
            "No archive gaps were detected under the current observation schedule."
        )
    graph = payload["graph"]
    lines.extend(
        [
            "",
            "## Evidence graph",
            "",
            f"- Nodes: `{len(graph['nodes'])}`",
            f"- Edges: `{len(graph['edges'])}`",
            "",
        ]
    )
    lines.extend(
        [
            "## Analyst note",
            "",
            payload["archival_relic"],
            "",
            "## Limitations",
            "",
            "Liminal records public observations. It does not establish intent, guilt, ownership, causality, or truth solely from repetition, deletion, timing, or association. Human review and primary-source verification remain required.",
            "",
        ]
    )
    return "\n".join(lines)


def write_reports(
    workspace: InvestigationWorkspace, output_dir: str | Path
) -> dict[str, Path]:
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    markdown_path = destination / "investigation.md"
    json_path = destination / "investigation.json"
    markdown_path.write_text(build_markdown_report(workspace), encoding="utf-8")
    json_path.write_text(
        json.dumps(workspace.report_payload(), indent=2, sort_keys=True, default=str)
        + "\n",
        encoding="utf-8",
    )
    return {"markdown": markdown_path, "json": json_path}
