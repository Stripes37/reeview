from __future__ import annotations

import json
from typing import Dict


def export_canva(album: Dict, out_path: str) -> None:
    data = {
        "Album": album.get("album"),
        "Artist": album.get("artist"),
        "Favourite": album.get("favourite_song"),
        "LeastFavourite": album.get("least_favourite_song"),
        "BestMoment": album.get("best_moment"),
        "BestProduction": album.get("best_production", {}).get("track"),
        "BestFeature": album.get("best_feature", {}).get("artist"),
        "FinalScore": str(album.get("final_score")) if album.get("final_score") is not None else None,
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def export_capcut(album: Dict, out_path: str) -> None:
    data = {
        "text_intro": album.get("album"),
        "text_tracklist": ", ".join(t.get("title") for t in album.get("tracklist", [])),
        "text_score": str(album.get("final_score")),
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
