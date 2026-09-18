#!/usr/bin/env python3
"""stdio MCP server: search MV 2026 Wahlprogramme (retrieval only, no recommender)."""

from __future__ import annotations

import json
import sys
from typing import Any

from mcp.server.mcpserver import MCPServer

from mv_wahl_mcp import search as S

mcp = MCPServer(
    "mv-wahl-mcp",
    instructions=(
        "Search and retrieve text from Wahlprogramme (election platforms) of all 19 "
        "parties admitted to the Mecklenburg-Vorpommern Landtagswahl 2026, plus the "
        "official bpb Wahl-O-Mat MV 2026 theses/answers as a secondary corpus. "
        "This is retrieval only — do NOT compute voting recommendations or closeness scores."
    ),
)


@mcp.tool()
def list_parties() -> list[dict[str, Any]]:
    """List all 19 parties with indexing status, source notes, and chunk counts."""
    return S.list_parties()


@mcp.tool()
def search_programmes(
    query: str,
    party: str | None = None,
    corpus: str | None = None,
    limit: int = 10,
) -> dict[str, Any]:
    """Keyword/FTS search across Wahlprogramme (and optionally Wahl-O-Mat answers).

    Args:
        query: Search terms in German or English (e.g. "Wohnungsbau", "Energiewende").
        party: Optional party filter (id or short name, e.g. "SPD", "GRÜNE", "Die Linke").
        corpus: Optional "programme" (full platforms) or "wahlomat" (theses + answers).
        limit: Max hits (1–50, default 10).
    """
    try:
        hits = S.search_programmes(query=query, party=party, corpus=corpus, limit=limit)
    except ValueError as e:
        return {"error": str(e), "results": []}
    return {
        "query": query,
        "party_filter": party,
        "corpus_filter": corpus,
        "count": len(hits),
        "results": hits,
    }


@mcp.tool()
def get_party_programme(
    party: str,
    offset: int = 0,
    limit: int = 5,
    corpus: str = "programme",
) -> dict[str, Any]:
    """Fetch sequential text chunks from one party's programme (or Wahl-O-Mat answers).

    Args:
        party: Party id or short name (e.g. "CDU", "Volt", "BSW").
        offset: Chunk offset (0-based).
        limit: Number of chunks to return (1–50).
        corpus: "programme" (default) or "wahlomat".
    """
    try:
        return S.get_party_programme(party=party, offset=offset, limit=limit, corpus=corpus)
    except ValueError as e:
        return {"error": str(e)}


@mcp.tool()
def coverage_status() -> dict[str, Any]:
    """Return coverage table: which of the 19 parties are indexed and source notes."""
    parties = S.list_parties()
    return {
        "election": "Landtagswahl Mecklenburg-Vorpommern 2026",
        "parties_total": 19,
        "parties_indexed": sum(1 for p in parties if p["indexed"]),
        "parties": [
            {
                "id": p["id"],
                "name": p["short_name"],
                "indexed": bool(p["indexed"]),
                "chars": p["char_count"],
                "chunks": p["chunk_count"],
                "source": p["source_url"],
                "note": p["source_note"],
            }
            for p in parties
        ],
        "note": (
            "Primary corpus = full Wahlprogramme. Secondary = bpb Wahl-O-Mat MV 2026 "
            "dataset (theses + party answers). Not a voting recommender."
        ),
    }


def main() -> None:
    # Ensure index exists before serving
    try:
        S.connect().close()
    except FileNotFoundError as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
