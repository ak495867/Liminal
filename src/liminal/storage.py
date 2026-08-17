from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Iterable

from .models import Claim, Entity, ProvenanceEdge, SourceSnapshot


class SnapshotStore:
    def __init__(self, path: str | Path = "liminal.db") -> None:
        self.path = str(path)
        self.connection = sqlite3.connect(self.path)
        self.connection.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self) -> None:
        self.connection.executescript(
            """
            create table if not exists snapshots (
                id integer primary key,
                source_url text not null,
                observed_at text not null,
                published_at text,
                title text,
                content text not null,
                content_hash text not null,
                semantic_hash text not null,
                source_type text not null,
                status_code integer,
                content_type text,
                metadata_json text not null
            );
            create index if not exists idx_snapshots_url_time on snapshots(source_url, observed_at);
            create table if not exists claims (
                claim_id text primary key,
                text text not null,
                source_url text not null,
                observed_at text not null,
                confidence real not null,
                subject text,
                predicate text,
                object_value text,
                quoted_text text,
                evidence_hash text
            );
            create table if not exists entities (
                entity_id text primary key,
                canonical_name text not null,
                entity_type text not null,
                aliases_json text not null,
                attributes_json text not null,
                confidence real not null
            );
            create table if not exists provenance_edges (
                edge_id text primary key,
                source_id text not null,
                target_id text not null,
                relation text not null,
                observed_at text not null,
                confidence real not null,
                evidence_url text,
                metadata_json text not null
            );
            create index if not exists idx_edges_source on provenance_edges(source_id);
            create index if not exists idx_edges_target on provenance_edges(target_id);
            """
        )
        self.connection.commit()

    def save_snapshot(self, snapshot: SourceSnapshot) -> int:
        snapshot.validate()
        cursor = self.connection.execute(
            "insert into snapshots(source_url, observed_at, published_at, title, content, content_hash, semantic_hash, source_type, status_code, content_type, metadata_json) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (snapshot.source_url, snapshot.observed_at.isoformat(), snapshot.published_at.isoformat() if snapshot.published_at else None, snapshot.title, snapshot.content, snapshot.content_hash, snapshot.semantic_hash, snapshot.source_type, snapshot.status_code, snapshot.content_type, json.dumps(snapshot.metadata, sort_keys=True, default=str)),
        )
        self.connection.commit()
        return int(cursor.lastrowid)

    def save_claim(self, claim: Claim) -> None:
        claim.validate()
        self.connection.execute(
            "insert or replace into claims(claim_id, text, source_url, observed_at, confidence, subject, predicate, object_value, quoted_text, evidence_hash) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (claim.claim_id, claim.text, claim.source_url, claim.observed_at.isoformat(), claim.confidence, claim.subject, claim.predicate, claim.object_value, claim.quoted_text, claim.evidence_hash),
        )
        self.connection.commit()

    def save_entity(self, entity: Entity) -> None:
        entity.validate()
        self.connection.execute(
            "insert or replace into entities(entity_id, canonical_name, entity_type, aliases_json, attributes_json, confidence) values (?, ?, ?, ?, ?, ?)",
            (entity.entity_id, entity.canonical_name, entity.entity_type, json.dumps(entity.aliases), json.dumps(entity.attributes, sort_keys=True, default=str), entity.confidence),
        )
        self.connection.commit()

    def save_edge(self, edge_id: str, edge: ProvenanceEdge) -> None:
        edge.validate()
        self.connection.execute(
            "insert or replace into provenance_edges(edge_id, source_id, target_id, relation, observed_at, confidence, evidence_url, metadata_json) values (?, ?, ?, ?, ?, ?, ?, ?)",
            (edge_id, edge.source_id, edge.target_id, edge.relation, edge.observed_at.isoformat(), edge.confidence, edge.evidence_url, json.dumps(edge.metadata, sort_keys=True, default=str)),
        )
        self.connection.commit()

    def snapshots_for_url(self, source_url: str) -> list[sqlite3.Row]:
        rows = self.connection.execute("select * from snapshots where source_url = ? order by observed_at", (source_url,)).fetchall()
        return list(rows)

    def all_snapshots(self) -> list[sqlite3.Row]:
        return list(self.connection.execute("select * from snapshots order by observed_at").fetchall())

    def all_claims(self) -> list[sqlite3.Row]:
        return list(self.connection.execute("select * from claims order by observed_at").fetchall())

    def all_entities(self) -> list[sqlite3.Row]:
        return list(self.connection.execute("select * from entities order by canonical_name").fetchall())

    def all_edges(self) -> list[sqlite3.Row]:
        return list(self.connection.execute("select * from provenance_edges order by observed_at").fetchall())

    def close(self) -> None:
        self.connection.close()

    def __enter__(self) -> SnapshotStore:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
