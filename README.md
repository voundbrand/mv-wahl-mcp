# mv-wahl-mcp

MCP server for **searching and retrieving** the Wahlprogramme (election platforms) of all **19** parties admitted to the **Landtagswahl Mecklenburg-Vorpommern 2026**.

This is **retrieval only** — not a Wahl-O-Mat clone and not a voting recommender. Do not use it to compute “closeness” scores from user positions.

Built for Martin Müller / Remington S.: let a KI browse full party programmes (primary) plus the official bpb Wahl-O-Mat MV 2026 theses & answers (secondary corpus).

## Features

| Tool | Purpose |
|------|---------|
| `list_parties` | All 19 parties + indexing status |
| `search_programmes` | FTS5 keyword search (`query`, optional `party`, `corpus`) |
| `get_party_programme` | Fetch sequential chunks for one party |
| `coverage_status` | Coverage table (source → indexed) |

Corpora:

- `programme` — full / website-captured Wahlprogramme (primary)
- `wahlomat` — bpb Wahl-O-Mat MV 2026 dataset (theses + party answers)

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .

# Rebuild FTS index from extracted texts + Wahl-O-Mat xlsx
python scripts/build_index.py

# Run MCP server (stdio)
python -m mv_wahl_mcp.server
# or:
mv-wahl-mcp
```

Smoke-test search without MCP:

```bash
python -c "
from mv_wahl_mcp.search import search_programmes
import json
print(json.dumps(search_programmes('Wohnungsbau', limit=5), ensure_ascii=False, indent=2))
"
```

## Cursor / Claude Desktop MCP config

### Cursor (`~/.cursor/mcp.json` or project `.cursor/mcp.json`)

```json
{
  "mcpServers": {
    "mv-wahl": {
      "command": "/ABSOLUTE/PATH/mv-wahl-mcp/.venv/bin/python",
      "args": ["-m", "mv_wahl_mcp.server"],
      "cwd": "/ABSOLUTE/PATH/mv-wahl-mcp",
      "env": {
        "PYTHONPATH": "/workspace/mv-wahl-mcp/src"
      }
    }
  }
}
```

If you move the project, point `command` / `cwd` at your local clone and use that venv’s Python.

### Claude Desktop (`claude_desktop_config.json`)

```json
{
  "mcpServers": {
    "mv-wahl": {
      "command": "/ABSOLUTE/PATH/mv-wahl-mcp/.venv/bin/python",
      "args": ["-m", "mv_wahl_mcp.server"],
      "cwd": "/ABSOLUTE/PATH/mv-wahl-mcp",
      "env": {
        "PYTHONPATH": "/ABSOLUTE/PATH/mv-wahl-mcp/src"
      }
    }
  }
}
```

## Data layout

```
data/
  parties.json          # metadata + source URLs for all 19
  programmes/           # PDF sources
  programmes_text/      # pdftotext extracts
  wahlomat/             # bpb Datensatz zip + xlsx
  index.db              # SQLite + FTS5 (built by scripts/build_index.py)
```

### Wahl-O-Mat dataset

Downloaded from the bpb download page:

- https://www.bpb.de/themen/wahl-o-mat/mecklenburg-vorpommern-2026/579912/download/
- File: `Wahl-O-Mat_Mecklenburg-Vorpommern_2026_Datensatz.zip`

bpb licence restricts creating Wahl-O-Mat-like recommenders from the dataset; this project only indexes text for search/retrieval (journalistic/research-style analysis).

### Programme sources

Prefer official party / Landesverband PDFs where available. Many smaller parties are mirrored via the schwerin.news Aug 2026 aggregation of all admitted lists:

- https://schwerin.news/2026/08/19/alle-wahlprogramme-zur-anstehenden-landtagswahl-in-mv/

See `data/parties.json` and the `coverage_status` tool for per-party notes. Short / website-captured texts (e.g. Die PARTEI, WLD, Team Freiheit, Handwerker 10-Punkte) are documented honestly.

## Re-extract / re-index

```bash
# Needs poppler-utils (pdftotext)
for f in data/programmes/*.pdf; do
  base=$(basename "$f" .pdf)
  pdftotext -layout "$f" "data/programmes_text/${base}.txt"
done
python scripts/build_index.py
```

## Licence / ethics

- Party programmes remain copyright of the respective parties.
- Wahl-O-Mat dataset © Bundeszentrale für politische Bildung — see `data/wahlomat/Hinweis.txt`.
- This tool must not be turned into a proximity/voting recommender.

## Start command (summary)

```bash
./run.sh
```

Or via Cursor MCP config pointing at `./run.sh` (or the venv python `-m mv_wahl_mcp.server`).

## Coverage (build-time snapshot)

All **19/19** admitted Landeslisten are indexed. Volume varies:

| Party | Chars (approx) | Notes |
|-------|----------------|-------|
| SPD, AfD, CDU, Die Linke, GRÜNE, FDP, BSW, Volt | large full programmes | Official / Landesverband PDFs |
| Tierschutzpartei, FREIE WÄHLER, Bündnis C, PdF, KPD | medium | Official or aggregator PDFs |
| PIRATEN, ÖDP | shorter full programmes | Official / aggregator |
| Die PARTEI, Team Freiheit, WLD | website captures | No long PDF published |
| Handwerker Partei Deutschland | short 10-point PDF | Intentional short programme |

Secondary corpus: **722** Wahl-O-Mat position rows (38 theses × 19 parties) from the official bpb dataset.
