from __future__ import annotations


def export_md(album: dict, out_path: str) -> None:
    genre_tags = " ".join(f"#{g.replace(' ', '')}" for g in album.get("genre", []))
    content = (
        f"**Album Review:** {album.get('album')} — {album.get('artist')}\n\n"
        f"Fav: {album.get('favourite_song')}\n"
        f"Least: {album.get('least_favourite_song')}\n"
        f"Best moment: {album.get('best_moment')}\n"
        f"Score: {album.get('final_score')}/10\n\n"
        f"#AlbumReview {genre_tags}\n"
    )
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(content)
