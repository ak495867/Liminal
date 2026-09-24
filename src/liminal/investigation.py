from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Iterable

from .claims import extract_claims, extract_entities
from .gaps import detect_gaps
from .graph import EvidenceGraph
from .models import Claim, Entity, Investigation, ProvenanceEdge, SourceSnapshot
from .semantic_diff import SemanticDiff, compare_text
from .storage import SnapshotStore


class InvestigationWorkspace:
    def __init__(
        self, investigation: Investigation, store: SnapshotStore | None = None
    ) -> None:
        investigation.validate()
        self.investigation = investigation
        self.store = store or SnapshotStore(":memory:")
        self.graph = EvidenceGraph()
        self.snapshots: list[SourceSnapshot] = []
        self.claims: list[Claim] = []
        self.entities: list[Entity] = []
        self.diffs: list[SemanticDiff] = []

    def ingest_snapshot(self, snapshot: SourceSnapshot) -> list[Claim]:
        snapshot.validate()
        self.snapshots.append(snapshot)
        snapshot_node = f"snapshot_{snapshot.content_hash[:20]}"
        self.investigation.snapshot_ids.append(snapshot_node)
        self.graph.add_node(
            snapshot_node,
            "snapshot",
            source_url=snapshot.source_url,
            observed_at=snapshot.observed_at.isoformat(),
            semantic_hash=snapshot.semantic_hash,
        )
        self.graph.add_node(snapshot.source_url, "source", url=snapshot.source_url)
        edge_id = f"edge_source_{snapshot.content_hash[:20]}"
        self.graph.add_edge(
            edge_id,
            ProvenanceEdge(
                source_id=snapshot.source_url,
                target_id=snapshot_node,
                relation="observed_as",
                observed_at=snapshot.observed_at,
                confidence=1.0,
                evidence_url=snapshot.source_url,
            ),
        )
        self.store.save_snapshot(snapshot)
        claims = extract_claims(
            snapshot.content, snapshot.source_url, snapshot.observed_at
        )
        entities = extract_entities(snapshot.content)
        for claim in claims:
            self.add_claim(claim, snapshot_node)
        for entity in entities:
            self.add_entity(entity, snapshot_node)
        return claims

    def add_claim(self, claim: Claim, snapshot_node: str | None = None) -> None:
        claim.validate()
        self.claims.append(claim)
        self.investigation.claim_ids.append(claim.claim_id)
        self.store.save_claim(claim)
        self.graph.add_node(
            claim.claim_id,
            "claim",
            text=claim.text,
            source_url=claim.source_url,
            confidence=claim.confidence,
        )
        if snapshot_node:
            edge_id = f"edge_{snapshot_node}_{claim.claim_id}"
            self.graph.add_edge(
                edge_id,
                ProvenanceEdge(
                    source_id=snapshot_node,
                    target_id=claim.claim_id,
                    relation="contains_claim",
                    observed_at=claim.observed_at,
                    confidence=claim.confidence,
                    evidence_url=claim.source_url,
                ),
            )
            self.investigation.edge_ids.append(edge_id)

    def add_entity(self, entity: Entity, snapshot_node: str | None = None) -> None:
        entity.validate()
        if entity.entity_id not in {item.entity_id for item in self.entities}:
            self.entities.append(entity)
            self.investigation.entity_ids.append(entity.entity_id)
            self.store.save_entity(entity)
        self.graph.add_node(
            entity.entity_id,
            "entity",
            canonical_name=entity.canonical_name,
            entity_type=entity.entity_type,
            confidence=entity.confidence,
        )
        if snapshot_node:
            edge_id = f"edge_{snapshot_node}_{entity.entity_id}"
            self.graph.add_edge(
                edge_id,
                ProvenanceEdge(
                    source_id=snapshot_node,
                    target_id=entity.entity_id,
                    relation="mentions",
                    observed_at=self.investigation.created_at,
                    confidence=entity.confidence,
                ),
            )
            self.investigation.edge_ids.append(edge_id)

    def compare_latest(self, source_url: str) -> SemanticDiff | None:
        versions = [
            snapshot for snapshot in self.snapshots if snapshot.source_url == source_url
        ]
        if len(versions) < 2:
            return None
        ordered = sorted(versions, key=lambda item: item.observed_at)
        diff = compare_text(ordered[-2].content, ordered[-1].content)
        self.diffs.append(diff)
        return diff

    def link_copy(
        self,
        source_claim_id: str,
        copied_claim_id: str,
        observed_at: datetime,
        confidence: float = 0.5,
    ) -> str:
        edge_id = f"copy_{source_claim_id}_{copied_claim_id}"
        self.graph.add_edge(
            edge_id,
            ProvenanceEdge(
                source_id=source_claim_id,
                target_id=copied_claim_id,
                relation="copies",
                observed_at=observed_at,
                confidence=confidence,
            ),
        )
        self.investigation.edge_ids.append(edge_id)
        return edge_id

    def archive_gaps(self):
        return detect_gaps(self.snapshots)

    def report_payload(self) -> dict[str, object]:
        return {
            "investigation": asdict(self.investigation),
            "snapshot_count": len(self.snapshots),
            "claim_count": len(self.claims),
            "entity_count": len(self.entities),
            "diff_count": len(self.diffs),
            "archive_gaps": [asdict(gap) for gap in self.archive_gaps()],
            "graph": self.graph.to_json_ready(),
            "archival_relic": "A claim can travel farther than its source, but not necessarily wiser.",
        }
