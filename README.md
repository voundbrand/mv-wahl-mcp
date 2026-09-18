# mv-wahl-mcp

MCP server for **searching and retrieving** the Wahlprogramme (election platforms) of all **19** parties admitted to the **Landtagswahl Mecklenburg-Vorpommern 2026**.

This is **retrieval only** — not a Wahl-O-Mat clone and not a voting recommender. Do not use it to compute "closeness" scores from user positions.

Built for Martin Müller / Remington S.: let a KI browse full party programmes (primary) plus the official bpb Wahl-O-Mat MV 2026 theses & answers (secondary corpus).

## Quick start

```bash
git clone https://github.com/voundbrand/mv-wahl-mcp.git
cd mv-wahl-mcp
./run.sh
```

That's it. The script creates a virtual environment if needed, installs dependencies, and starts the MCP server. The pre-built search index is included — no rebuild required.

**Requirements:** Python 3.11+

## Add to Cursor or Claude Desktop

Run `./run.sh --print-config` to get a ready-to-paste MCP configuration:

```bash
./run.sh --print-config
```

Copy the output into your MCP config file:

- **Cursor:** `~/.cursor/mcp.json` or `.cursor/mcp.json` in your project
- **Claude Desktop:** `claude_desktop_config.json`

If you already have other MCP servers configured, merge the `mv-wahl` entry into your existing `mcpServers` object.

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

## Test search without MCP

```bash
./run.sh &  # or skip if you just want to test the search module
cd mv-wahl-mcp
source .venv/bin/activate
python -c "
from mv_wahl_mcp.search import search_programmes
import json
print(json.dumps(search_programmes('Wohnungsbau', limit=5), ensure_ascii=False, indent=2))
"
```

## Data layout

```
data/
  parties.json          # metadata + source URLs for all 19
  programmes/           # PDF sources
  programmes_text/      # pdftotext extracts
  wahlomat/             # bpb Datensatz zip + xlsx
  index.db              # SQLite + FTS5 (pre-built, ready to use)
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

## Re-extract / re-index (optional)

Only needed if you modify the source PDFs or Wahl-O-Mat data:

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
