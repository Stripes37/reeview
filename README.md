# Album Review Tracker (Python + JSON)

A clear roadmap/guide/readme for building a **simple, local-first Python + JSON tool** to manage your album reviews and the **production stages** of each short-form video (Reels/Shorts/TikTok). Designed so a coding assistant (e.g., Codex) can implement it quickly.

---

## 0) Goals & Constraints

**Goals**

* Track each album review with consistent fields used in your videos.
* Store data in human-readable **JSON**.
* Provide a **CLI** (command-line interface) for fast, repeatable actions.
* Model the end-to-end **production pipeline** with explicit stages and timestamps.
* Export data for content scheduling and asset generation.

**Non-goals (for v1)**

* No web UI or database server.
* No external API auth.
* No audio/video processing.

**Constraints**

* Runs locally with Python 3.10+.
* Single JSON file (or one per album) under a `/data` directory.
* Minimal dependencies (standard library preferred).

---

## 1) Feature Summary

* **Create / read / update** album entries.
* **Tracklist + per-track ratings** collection.
* Derived fields (e.g., average track score, total runtime if provided).
* **Production stage state machine** with audit trail.
* Tagging and search (by artist, year, status, etc.).
* **Quick exports**:

  * CSV/JSON for schedulers (Later/Buffer/Metricool).
  * JSON for Canva/CapCut variable fills.
  * Markdown snippet for video description/caption.

---

## 2) Data Model (JSON)

One file `database.json` containing a top-level object:

```json
{
  "meta": {
    "version": 1,
    "created_at": "2025-08-20T12:00:00Z",
    "updated_at": "2025-08-20T12:00:00Z"
  },
  "albums": []
}
```

Each **album** entry:

```json
{
  "id": "2025-08-20-kendrick-lamar-to-pimp-a-butterfly",
  "artist": "Kendrick Lamar",
  "album": "To Pimp a Butterfly",
  "release_date": "2015-03-15",
  "genre": ["Hip-Hop", "Jazz Rap"],
  "cover_image_path": "assets/covers/to_pimp_a_butterfly.jpg",
  "links": {
    "spotify": "",
    "apple_music": "",
    "youtube_music": ""
  },
  "tracklist": [
    { "track_no": 1, "title": "Wesley's Theory", "rating": 8.5, "duration_sec": 294 },
    { "track_no": 2, "title": "For Free? (Interlude)", "rating": 7.5, "duration_sec": 130 }
  ],
  "favourite_song": "Alright",
  "least_favourite_song": "For Sale? (Interlude)",
  "best_moment": "The sax run at 2:48 on 'u'.",
  "best_production": {
    "track": "The Blacker the Berry",
    "producer": ["Boi-1da", "KOZ"]
  },
  "best_feature": {
    "artist": "George Clinton",
    "track": "Wesley's Theory"
  },
  "final_score": 9.2,
  "review_notes": "2–3 concise bullet points to voiceover.",
  "tags": ["classic", "social commentary"],

  "status": {
    "stage": "SCRIPTED",
    "history": [
      { "from": null, "to": "IDEATION", "at": "2025-08-18T14:00:00Z", "note": "Added album" },
      { "from": "IDEATION", "to": "SCRIPTED", "at": "2025-08-19T20:31:00Z", "note": "Wrote bullets" }
    ]
  },

  "timing": {
    "intro_sec": 3,
    "tracklist_sec": 10,
    "favourite_sec": 5,
    "least_favourite_sec": 5,
    "best_moment_sec": 10,
    "best_production_sec": 5,
    "best_feature_sec": 5,
    "outro_sec": 5
  },

  "assets": {
    "project_files": [],
    "export_paths": [],
    "thumbnails": []
  },

  "audit": {
    "created_at": "2025-08-18T14:00:00Z",
    "updated_at": "2025-08-19T20:31:00Z",
    "updated_by": "cli@local"
  }
}
```

**Notes**

* `id` is a slug: `YYYY-MM-DD-artist-album` (lowercase, hyphenated, ASCII-only).
* `genre` is a list for multi-genre support.
* `tracklist.rating` is numeric (0–10, one decimal allowed). `duration_sec` optional.
* `status.stage` is managed by a **state machine** (see below).

---

## 3) Production Stages (State Machine)

**Stage enum** (string):

* `IDEATION` → considering, listening phase
* `SCRIPTED` → bullets finalized
* `GRAPHICS_READY` → Canva/CapCut graphics done
* `VO_READY` → voiceover recorded (or TTS ready)
* `EDITING` → assembling timeline
* `SCHEDULED` → upload scheduled
* `PUBLISHED` → live
* `ARCHIVED` → retired/locked

**Allowed transitions** (direct):

```
IDEATION → SCRIPTED
SCRIPTED → GRAPHICS_READY
GRAPHICS_READY → VO_READY
VO_READY → EDITING
EDITING → SCHEDULED
SCHEDULED → PUBLISHED
PUBLISHED → ARCHIVED

# Flexible backsteps allowed with note:
SCRIPTED → IDEATION
GRAPHICS_READY → SCRIPTED
VO_READY → GRAPHICS_READY
EDITING → VO_READY
SCHEDULED → EDITING
```

**Validation rules**

* Stage must be a valid enum.
* Transition must be in `ALLOWED` set (unless `--force` flag is used; always record a history note).
* Every transition appends to `status.history` with timestamp + note.

---

## 4) Repo/File Layout

```
album-review-tracker/
├─ README.md
├─ tracker.py              # CLI entrypoint (argparse)
├─ models.py               # dataclasses, validation, enums
├─ storage.py              # JSON load/save, migrations, id/slug utils
├─ exporters/
│  ├─ csv_exporter.py      # to CSV for schedulers
│  ├─ json_exporter.py     # filtered JSON for Canva/CapCut
│  └─ md_exporter.py       # caption/description markdown
├─ utils/
│  ├─ search.py            # search/filter helpers
│  └─ time.py              # iso8601 helpers
├─ data/
│  └─ database.json        # main data store
└─ tests/
   ├─ test_models.py
   ├─ test_storage.py
   └─ test_cli.py
```

---

## 5) CLI Design (argparse)

All commands operate on `data/database.json` by default (configurable with `--db`).

### 5.1 Init & Health

* `python tracker.py init` → creates `data/database.json` if missing.
* `python tracker.py check` → validates JSON schema & cross-fields.

### 5.2 Create & Edit Albums

* `python tracker.py add --artist "Artist" --album "Title" --release-date 2024-10-01 --genre "Hip-Hop,Jazz" --cover assets/covers/title.jpg`
* `python tracker.py set-field --id <album_id> --field favourite_song --value "Track Name"`
* `python tracker.py add-track --id <album_id> --track-no 1 --title "Intro" --rating 7.5 --duration 123`
* `python tracker.py set-track-rating --id <album_id> --track-no 1 --rating 8.0`
* `python tracker.py bulk-import --csv path/to/albums.csv` (optional v1.1)

### 5.3 Stages

* `python tracker.py set-stage --id <album_id> --to GRAPHICS_READY --note "Canva done"`
* `python tracker.py back --id <album_id> --to SCRIPTED --note "Rewrite bullets"`
* `python tracker.py timeline --id <album_id>` → print stage history.

### 5.4 Listing & Search

* `python tracker.py list --stage EDITING`
* `python tracker.py list --artist "Kendrick Lamar"`
* `python tracker.py list --tag classic --sort updated_at:desc --limit 20`
* `python tracker.py find --query "butterfly"` (fuzzy search on artist/album)

### 5.5 Derived & Reports

* `python tracker.py stats --id <album_id>` → avg track rating, count, top/low track.
* `python tracker.py dashboard` → counts per stage, mean final_score by genre, etc.

### 5.6 Exports

* `python tracker.py export csv --out exports/scheduler.csv --fields id,artist,album,final_score,status.stage`
* `python tracker.py export json --template canva --out exports/canva.json --id <album_id>`
* `python tracker.py export md --id <album_id> --out exports/<id>.md` → caption stub.

### 5.7 Safety

* `python tracker.py snapshot` → writes `data/snapshots/<timestamp>.json` (backup).
* `python tracker.py migrate` → schema version bump with safe transforms.

---

## 6) Schema & Validation Details

**Album fields**

* `artist`/`album`: non-empty strings; stored in Title Case; slug generated.
* `release_date`: `YYYY-MM-DD`; optional if unknown.
* `genre`: 1–5 strings; normalized capitalization.
* `tracklist`: 1–50 items, `track_no` unique; `rating` `0–10` with `0.1` increments.
* `favourite_song`/`least_favourite_song`: must exist in `tracklist.title` (warn if not).
* `best_production.producer`: one or more strings.
* `final_score`: `0–10`, keep one decimal.
* `timing.*_sec`: positive ints; total recommended 45–60s.

**Database rules**

* Unique `id` across `albums`.
* `audit.updated_at` refreshed on every write.
* `status.history[*]` monotonic timestamps.

---

## 7) Implementation Outline (Python)

### 7.1 `models.py`

* Define `Enum Stage(Enum)` with members above.
* `@dataclass Track { track_no:int; title:str; rating:float|None; duration_sec:int|None }`
* `@dataclass BestProduction { track:str; producer:list[str] }`
* `@dataclass BestFeature { artist:str; track:str }`
* `@dataclass Status { stage:Stage; history:list[Transition] }`
* `@dataclass Album {...}` (fields from schema) + methods:

  * `validate(self) -> list[str]` (return warnings/errors)
  * `average_track_rating(self) -> float|None`
  * `top_track(self) -> Track|None`, `low_track(self) -> Track|None`
  * `to_dict()/from_dict()`

### 7.2 `storage.py`

* `load_db(path) -> dict` (creates default if missing).
* `save_db(path, data)` (pretty JSON, sort keys).
* `generate_id(date, artist, album) -> str` (slugify).
* `find_album(db, id) -> dict`
* `upsert_album(db, album_dict)`
* `snapshot(db)`

### 7.3 `tracker.py` (CLI)

* Use `argparse` subparsers: `init`, `add`, `set-field`, `add-track`, `set-track-rating`, `set-stage`, `list`, `find`, `stats`, `export`, `snapshot`, `migrate`.
* Each command:

  1. load DB
  2. mutate/query
  3. validate
  4. save DB
  5. print concise result

### 7.4 `exporters/`

* **csv_exporter.py**: selected fields → CSV rows. Handles nested (e.g., `status.stage`).
* **json_exporter.py**: two templates:

  * `canva`: `{ "Album": ..., "Artist": ..., "Favourite": ..., "LeastFavourite": ..., "BestMoment": ..., "BestProduction": ..., "BestFeature": ..., "FinalScore": ... }`
  * `capcut`: a key-value map: `{ "text_intro": ..., "text_tracklist": ..., "text_score": ... }`
* **md_exporter.py**: caption template:

  ```md
  **Album Review:** {album} — {artist}\n
  Fav: {favourite_song}\nLeast: {least_favourite_song}\nBest moment: {best_moment}\nScore: {final_score}/10\n
  #AlbumReview #{genre_tags}
  ```

---

## 8) Example CLI Session

```bash
# 1) Initialize
python tracker.py init

# 2) Add an album
python tracker.py add \
  --artist "Kendrick Lamar" \
  --album "To Pimp a Butterfly" \
  --release-date 2015-03-15 \
  --genre "Hip-Hop,Jazz Rap" \
  --cover assets/covers/tpab.jpg

# 3) Add a few tracks with ratings
python tracker.py add-track --id 2015-03-15-kendrick-lamar-to-pimp-a-butterfly --track-no 1 --title "Wesley's Theory" --rating 8.5 --duration 294
python tracker.py add-track --id 2015-03-15-kendrick-lamar-to-pimp-a-butterfly --track-no 2 --title "For Free? (Interlude)" --rating 7.5 --duration 130

# 4) Set favorites and highlights
python tracker.py set-field --id 2015-03-15-kendrick-lamar-to-pimp-a-butterfly --field favourite_song --value "Alright"
python tracker.py set-field --id 2015-03-15-kendrick-lamar-to-pimp-a-butterfly --field best_moment --value "The sax run at 2:48 on 'u'"
python tracker.py set-field --id 2015-03-15-kendrick-lamar-to-pimp-a-butterfly --field final_score --value 9.2

# 5) Advance production stage
python tracker.py set-stage --id 2015-03-15-kendrick-lamar-to-pimp-a-butterfly --to SCRIPTED --note "Bullets done"
python tracker.py set-stage --id 2015-03-15-kendrick-lamar-to-pimp-a-butterfly --to GRAPHICS_READY --note "Canva complete"

# 6) Export assets for posting and templates
python tracker.py export md --id 2015-03-15-kendrick-lamar-to-pimp-a-butterfly --out exports/tpab.md
python tracker.py export json --template canva --out exports/tpab-canva.json --id 2015-03-15-kendrick-lamar-to-pimp-a-butterfly
python tracker.py export csv --out exports/scheduler.csv --fields id,artist,album,final_score,status.stage
```

---

## 9) Sample Outputs

**9.1 Caption (Markdown)**

```md
**Album Review:** To Pimp a Butterfly — Kendrick Lamar

Fav: Alright
Least: For Sale? (Interlude)
Best moment: The sax run at 2:48 on 'u'
Score: 9.2/10

#AlbumReview #HipHop #JazzRap
```

**9.2 Canva JSON (variables)**

```json
{
  "Album": "To Pimp a Butterfly",
  "Artist": "Kendrick Lamar",
  "Favourite": "Alright",
  "LeastFavourite": "For Sale? (Interlude)",
  "BestMoment": "The sax run at 2:48 on 'u'",
  "BestProduction": "The Blacker the Berry — Boi-1da, KOZ",
  "BestFeature": "George Clinton — Wesley's Theory",
  "FinalScore": "9.2"
}
```

**9.3 CSV (scheduler)**

```csv
id,artist,album,final_score,status.stage
2015-03-15-kendrick-lamar-to-pimp-a-butterfly,Kendrick Lamar,To Pimp a Butterfly,9.2,PUBLISHED
```

---

## 10) Error Handling & Edge Cases

* Duplicate `id` → reject add; suggest `--date` override.
* Missing favourite/least favourite in `tracklist` → warn.
* Ratings outside 0–10 → reject.
* Invalid stage transition → reject unless `--force` with note.
* Corrupt JSON → create `data/recovery-<timestamp>.json` and abort.

---

## 11) Testing Strategy

* **Unit tests** for: slugify, schema validation, stage transitions, exporters.
* **Golden files**: sample `database.json` fixtures for round-trip load/save.
* **CLI tests** (subprocess) to confirm exit codes and outputs.

---

## 12) Future Enhancements (Optional)

* YAML import/export.
* Per-album JSON files under `data/albums/<id>.json` with index.
* Simple `http.server` to serve a static dashboard (read-only).
* Notion/Google Sheets sync.
* Automatic thumbnail generator (Pillow) using your brand colors.
* Integration stubs for posting schedulers (export formats only, no API keys).

---

## 13) Coding Checklist (for Codex)

1. Create repo layout exactly as in §4.
2. Implement `models.py` dataclasses + `Stage` enum + validation.
3. Implement `storage.py` (load/save/migrate/slugify/find/upsert/snapshot).
4. Implement `tracker.py` CLI with subcommands in §5.
5. Implement exporters in §7.4 with templates in §9.
6. Add tests in `tests/` covering success + failures.
7. Provide example `data/database.json` pre-populated with 2–3 albums.
8. Ensure `python tracker.py check` passes on examples.
9. Document commands in `README.md` with usage examples.

---

## 14) Quick Start

```bash
python -m venv .venv && source .venv/bin/activate
python -m pip install --upgrade pip
# No third-party deps required for v1
python tracker.py init
python tracker.py add --artist "Artist" --album "Album" --release-date 2024-01-01 --genre "Hip-Hop" --cover assets/covers/album.jpg
python tracker.py list --stage IDEATION
```

**You’re set.** This gives you a lightweight, automation-friendly spine to populate Canva/CapCut and your posting scheduler from one source of truth.

### Simple GUI

Run a basic desktop interface with:

```bash
python launcher.py
```

The GUI lets you view existing album IDs and add new albums without using the command line.


## Developer Instructions

- Run unit tests with `pytest`.
- Use `python tracker.py --db data/database.json <command>` for CLI actions.
- Exporters output files to provided paths; ensure directories exist.
- Snapshot command writes backups to `data/snapshots/`.
