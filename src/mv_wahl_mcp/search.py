"""SQLite FTS5 search helpers."""

from __future__ import annotations

import re
import sqlite3
from dataclasses import asdict, dataclass
from typing import Any

from mv_wahl_mcp.paths import INDEX_DB


@dataclass
class SearchHit:
    party_id: str
    party_short: str
    corpus: str
    title: str
    snippet: str
    chunk_index: int
    score: float | None = None


def connect() -> sqlite3.Connection:
    if not INDEX_DB.exists():
        raise FileNotFoundError(
            f"Index DB not found at {INDEX_DB}. Run: python scripts/build_index.py"
        )
    conn = sqlite3.connect(INDEX_DB)
    conn.row_factory = sqlite3.Row
    return conn


def _fts_query(raw: str) -> str:
    """Convert user query to FTS5 MATCH expression (OR of tokens + phrase)."""
    raw = raw.strip()
    if not raw:
        return ""
    # If user already uses FTS operators, pass through carefully
    if any(op in raw for op in ('"', " AND ", " OR ", " NOT ", "*")):
        return raw
    tokens = re.findall(r"[\wÄÖÜäöüß\-]+", raw, flags=re.UNICODE)
    tokens = [t for t in tokens if len(t) >= 2]
    if not tokens:
        return f'"{raw}"'
    # Prefer phrase match OR individual terms
    phrase = " ".join(tokens)
    parts = [f'"{phrase}"'] + [f"{t}*" if len(t) >= 4 else t for t in tokens]
    return " OR ".join(parts)


def list_parties() -> list[dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT id, short_name, full_name, source_url, source_note,
                   char_count, chunk_count, indexed
            FROM parties
            ORDER BY rowid
            """
        ).fetchall()
        return [dict(r) for r in rows]


def get_party(party: str) -> dict[str, Any] | None:
    with connect() as conn:
        row = conn.execute(
            """
            SELECT * FROM parties
            WHERE id = ? COLLATE NOCASE
               OR short_name = ? COLLATE NOCASE
               OR full_name = ? COLLATE NOCASE
            """,
            (party, party, party),
        ).fetchone()
        return dict(row) if row else None


def resolve_party_id(party: str | None) -> str | None:
    if not party:
        return None
    p = get_party(party)
    if p:
        return p["id"]
    # fuzzy
    key = party.casefold().strip()
    with connect() as conn:
        rows = conn.execute("SELECT id, short_name, full_name FROM parties").fetchall()
    for r in rows:
        if key in r["id"].casefold() or key in r["short_name"].casefold() or key in r["full_name"].casefold():
            return r["id"]
    return None


def search_programmes(
    query: str,
    party: str | None = None,
    corpus: str | None = None,
    limit: int = 10,
) -> list[dict[str, Any]]:
    fts = _fts_query(query)
    if not fts:
        return []
    party_id = resolve_party_id(party) if party else None
    if party and not party_id:
        raise ValueError(f"Unknown party: {party}")

    filters = []
    params: list[Any] = [fts]
    if party_id:
        filters.append("c.party_id = ?")
        params.append(party_id)
    if corpus in ("programme", "wahlomat"):
        filters.append("c.corpus = ?")
        params.append(corpus)
    where = (" AND " + " AND ".join(filters)) if filters else ""
    params.append(max(1, min(limit, 50)))

    sql = f"""
        SELECT
            c.party_id,
            p.short_name AS party_short,
            c.corpus,
            c.title,
            c.chunk_index,
            snippet(chunks_fts, 3, '>>>', '<<<', '…', 40) AS snippet,
            bm25(chunks_fts) AS score,
            c.text
        FROM chunks_fts
        JOIN chunks c ON c.id = chunks_fts.rowid
        JOIN parties p ON p.id = c.party_id
        WHERE chunks_fts MATCH ?{where}
        ORDER BY bm25(chunks_fts)
        LIMIT ?
    """
    with connect() as conn:
        try:
            rows = conn.execute(sql, params).fetchall()
        except sqlite3.OperationalError:
            # Fallback: LIKE search
            like = f"%{query}%"
            like_params: list[Any] = [like]
            like_filters = ["c.text LIKE ?"]
            if party_id:
                like_filters.append("c.party_id = ?")
                like_params.append(party_id)
            if corpus in ("programme", "wahlomat"):
                like_filters.append("c.corpus = ?")
                like_params.append(corpus)
            like_params.append(max(1, min(limit, 50)))
            rows = conn.execute(
                f"""
                SELECT c.party_id, p.short_name AS party_short, c.corpus, c.title,
                       c.chunk_index, substr(c.text, 1, 280) AS snippet,
                       NULL AS score, c.text
                FROM chunks c
                JOIN parties p ON p.id = c.party_id
                WHERE {" AND ".join(like_filters)}
                LIMIT ?
                """,
                like_params,
            ).fetchall()

    results = []
    for r in rows:
        snip = r["snippet"] or ""
        if ">>>" not in snip and r["text"]:
            # highlight manually for LIKE fallback
            idx = r["text"].casefold().find(query.casefold())
            if idx >= 0:
                a = max(0, idx - 80)
                b = min(len(r["text"]), idx + len(query) + 80)
                snip = ("…" if a else "") + r["text"][a:b] + ("…" if b < len(r["text"]) else "")
        results.append(
            {
                "party_id": r["party_id"],
                "party": r["party_short"],
                "corpus": r["corpus"],
                "title": r["title"],
                "chunk_index": r["chunk_index"],
                "snippet": snip,
                "score": float(r["score"]) if r["score"] is not None else None,
            }
        )
    return results


def get_party_programme(
    party: str,
    offset: int = 0,
    limit: int = 5,
    corpus: str = "programme",
) -> dict[str, Any]:
    party_id = resolve_party_id(party)
    if not party_id:
        raise ValueError(f"Unknown party: {party}")
    meta = get_party(party_id)
    assert meta is not None
    with connect() as conn:
        total = conn.execute(
            "SELECT COUNT(*) FROM chunks WHERE party_id=? AND corpus=?",
            (party_id, corpus),
        ).fetchone()[0]
        rows = conn.execute(
            """
            SELECT chunk_index, title, text
            FROM chunks
            WHERE party_id=? AND corpus=?
            ORDER BY chunk_index
            LIMIT ? OFFSET ?
            """,
            (party_id, corpus, max(1, min(limit, 50)), max(0, offset)),
        ).fetchall()
    return {
        "party": {
            "id": meta["id"],
            "short_name": meta["short_name"],
            "full_name": meta["full_name"],
            "source_url": meta["source_url"],
            "source_note": meta["source_note"],
            "char_count": meta["char_count"],
            "chunk_count": meta["chunk_count"],
        },
        "corpus": corpus,
        "offset": offset,
        "limit": limit,
        "total_chunks": total,
        "chunks": [dict(r) for r in rows],
    }
