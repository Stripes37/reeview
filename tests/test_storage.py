import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

import json
from pathlib import Path

from storage import generate_id, load_db, save_db, find_album, upsert_album


def test_generate_id_slug():
    album_id = generate_id("2024-01-01", "Kendrick Lamar", "To Pimp a Butterfly")
    assert album_id == "2024-01-01-kendrick-lamar-to-pimp-a-butterfly"


def test_load_save(tmp_path):
    db_path = tmp_path / "db.json"
    db = load_db(str(db_path))
    assert db["albums"] == []
    album = {"id": "1", "artist": "A", "album": "B"}
    upsert_album(db, album)
    save_db(str(db_path), db)
    db2 = load_db(str(db_path))
    assert find_album(db2, "1")
