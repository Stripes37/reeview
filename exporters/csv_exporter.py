from __future__ import annotations

import csv
from typing import List, Dict


def export_csv(albums: List[Dict], fields: List[str], out_path: str) -> None:
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for album in albums:
            row = {}
            for field in fields:
                if field == "status.stage":
                    row[field] = album.get("status", {}).get("stage")
                else:
                    row[field] = album.get(field)
            writer.writerow(row)
