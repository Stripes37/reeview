from __future__ import annotations

import json
from pathlib import Path
from typing import Dict
from datetime import datetime
import unicodedata
import re

from models import Album

ISO_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


def load_db(path: str) -> Dict:
    p = Path(path)
    if not p.exists():
        data = {"meta": {"version": 1, "created_at": datetime.utcnow().strftime(ISO_FORMAT), "updated_at": datetime.utcnow().strftime(ISO_FORMAT)}, "albums": []}
        save_db(path, data)
        return data
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_db(path: str, data: Dict) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    data["meta"]["updated_at"] = datetime.utcnow().strftime(ISO_FORMAT)
    with p.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)


def slugify(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^a-zA-Z0-9]+", "-", value)
    return value.strip("-").lower()


def generate_id(date: str, artist: str, album: str) -> str:
    return f"{date}-{slugify(artist)}-{slugify(album)}"


def find_album(db: Dict, album_id: str) -> Dict | None:
    for a in db.get("albums", []):
        if a["id"] == album_id:
            return a
    return None


def upsert_album(db: Dict, album_dict: Dict) -> None:
    existing = find_album(db, album_dict["id"])
    if existing:
        db["albums"][db["albums"].index(existing)] = album_dict
    else:
        db["albums"].append(album_dict)


def snapshot(db_path: str) -> Path:
    db = load_db(db_path)
    snap_dir = Path(db_path).parent / "snapshots"
    snap_dir.mkdir(parents=True, exist_ok=True)
    snap_path = snap_dir / f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.json"
    with snap_path.open("w", encoding="utf-8") as f:
        json.dump(db, f, indent=2, sort_keys=True)
    return snap_path
