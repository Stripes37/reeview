import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

import json
import subprocess
from pathlib import Path


def run(cmd):
    return subprocess.check_output(cmd, text=True)


def test_cli_add_and_list(tmp_path):
    db = tmp_path / "db.json"
    run(["python", "tracker.py", "--db", str(db), "init"])
    out = run(["python", "tracker.py", "--db", str(db), "add", "--artist", "Artist", "--album", "Album"])
    album_id = out.strip()
    out = run(["python", "tracker.py", "--db", str(db), "list"])
    assert album_id in out


def test_cli_set_stage(tmp_path):
    db = tmp_path / "db.json"
    run(["python", "tracker.py", "--db", str(db), "init"])
    album_id = run(["python", "tracker.py", "--db", str(db), "add", "--artist", "A", "--album", "B"]).strip()
    run(["python", "tracker.py", "--db", str(db), "set-stage", "--id", album_id, "--to", "SCRIPTED"])
    data = json.loads(Path(db).read_text())
    assert data["albums"][0]["status"]["stage"] == "SCRIPTED"
