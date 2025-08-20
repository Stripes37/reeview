from __future__ import annotations

from typing import List, Dict, Any


def filter_albums(albums: List[Dict[str, Any]], **criteria) -> List[Dict[str, Any]]:
    results = albums
    for key, value in criteria.items():
        if value is None:
            continue
        if key == "stage":
            results = [a for a in results if a.get("status", {}).get("stage") == value]
        elif key == "artist":
            results = [a for a in results if a.get("artist") == value]
        elif key == "tag":
            results = [a for a in results if value in a.get("tags", [])]
    return results


def search_query(albums: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
    q = query.lower()
    return [a for a in albums if q in a.get("artist", "").lower() or q in a.get("album", "").lower()]
