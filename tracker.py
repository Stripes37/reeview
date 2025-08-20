from __future__ import annotations

import argparse
from pathlib import Path
from typing import List

from models import Album, Track, Stage
from storage import load_db, save_db, generate_id, find_album, upsert_album, snapshot
from utils.time import now_iso
from utils.search import filter_albums, search_query
from exporters.csv_exporter import export_csv
from exporters.json_exporter import export_canva, export_capcut
from exporters.md_exporter import export_md

DB_DEFAULT = "data/database.json"


def cmd_init(args: argparse.Namespace) -> None:
    load_db(args.db)
    print(f"initialized {args.db}")


def cmd_check(args: argparse.Namespace) -> None:
    db = load_db(args.db)
    warnings = []
    for a in db.get("albums", []):
        album = Album.from_dict(a)
        warnings.extend(album.validate())
    if warnings:
        for w in warnings:
            print(w)
    else:
        print("ok")


def cmd_add(args: argparse.Namespace) -> None:
    db = load_db(args.db)
    album_id = generate_id(args.release_date or "0000-00-00", args.artist, args.album)
    if find_album(db, album_id):
        raise SystemExit("album exists")
    album = Album(
        id=album_id,
        artist=args.artist,
        album=args.album,
        release_date=args.release_date,
        genre=[g.strip() for g in (args.genre or "").split(",") if g.strip()],
        cover_image_path=args.cover,
        audit={"created_at": now_iso(), "updated_at": now_iso(), "updated_by": "cli"},
    )
    upsert_album(db, album.to_dict())
    save_db(args.db, db)
    print(album.id)


def cmd_set_field(args: argparse.Namespace) -> None:
    db = load_db(args.db)
    album = find_album(db, args.id)
    if not album:
        raise SystemExit("not found")
    album[args.field] = args.value
    album.setdefault("audit", {})["updated_at"] = now_iso()
    save_db(args.db, db)


def cmd_add_track(args: argparse.Namespace) -> None:
    db = load_db(args.db)
    album = find_album(db, args.id)
    if not album:
        raise SystemExit("not found")
    track = Track(track_no=args.track_no, title=args.title, rating=args.rating, duration_sec=args.duration)
    album.setdefault("tracklist", []).append(track.__dict__)
    save_db(args.db, db)


def cmd_set_track_rating(args: argparse.Namespace) -> None:
    db = load_db(args.db)
    album = find_album(db, args.id)
    if not album:
        raise SystemExit("not found")
    for t in album.get("tracklist", []):
        if t["track_no"] == args.track_no:
            t["rating"] = args.rating
    save_db(args.db, db)


def cmd_set_stage(args: argparse.Namespace) -> None:
    db = load_db(args.db)
    album = find_album(db, args.id)
    if not album:
        raise SystemExit("not found")
    status = album.setdefault("status", {"stage": Stage.IDEATION.value, "history": []})
    from_stage = Stage(status.get("stage", "IDEATION"))
    to_stage = Stage(args.to)
    allowed = Stage[to_stage.name]
    from models import ALLOWED_TRANSITIONS
    if to_stage not in ALLOWED_TRANSITIONS.get(from_stage, set()) and not args.force:
        raise SystemExit("invalid transition")
    status["history"].append({"from_stage": from_stage.value, "to_stage": to_stage.value, "at": now_iso(), "note": args.note or ""})
    status["stage"] = to_stage.value
    save_db(args.db, db)


def cmd_list(args: argparse.Namespace) -> None:
    db = load_db(args.db)
    albums = filter_albums(db.get("albums", []), stage=args.stage, artist=args.artist, tag=args.tag)
    for a in albums[: args.limit]:
        print(a["id"])  # simple listing


def cmd_find(args: argparse.Namespace) -> None:
    db = load_db(args.db)
    albums = search_query(db.get("albums", []), args.query)
    for a in albums:
        print(a["id"])


def cmd_stats(args: argparse.Namespace) -> None:
    db = load_db(args.db)
    album_dict = find_album(db, args.id)
    if not album_dict:
        raise SystemExit("not found")
    album = Album.from_dict(album_dict)
    avg = album.average_track_rating()
    top = album.top_track()
    low = album.low_track()
    print({"average": avg, "top": top.title if top else None, "low": low.title if low else None})


def cmd_export(args: argparse.Namespace) -> None:
    db = load_db(args.db)
    if args.format == "csv":
        export_csv(db.get("albums", []), args.fields.split(","), args.out)
    elif args.format == "json":
        album = find_album(db, args.id)
        if args.template == "canva":
            export_canva(album, args.out)
        else:
            export_capcut(album, args.out)
    elif args.format == "md":
        album = find_album(db, args.id)
        export_md(album, args.out)


def cmd_snapshot(args: argparse.Namespace) -> None:
    path = snapshot(args.db)
    print(path)


def main(argv: List[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default=DB_DEFAULT)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("init")
    p.set_defaults(func=cmd_init)

    p = sub.add_parser("check")
    p.set_defaults(func=cmd_check)

    p = sub.add_parser("add")
    p.add_argument("--artist", required=True)
    p.add_argument("--album", required=True)
    p.add_argument("--release-date")
    p.add_argument("--genre")
    p.add_argument("--cover")
    p.set_defaults(func=cmd_add)

    p = sub.add_parser("set-field")
    p.add_argument("--id", required=True)
    p.add_argument("--field", required=True)
    p.add_argument("--value", required=True)
    p.set_defaults(func=cmd_set_field)

    p = sub.add_parser("add-track")
    p.add_argument("--id", required=True)
    p.add_argument("--track-no", type=int, required=True)
    p.add_argument("--title", required=True)
    p.add_argument("--rating", type=float)
    p.add_argument("--duration", type=int)
    p.set_defaults(func=cmd_add_track)

    p = sub.add_parser("set-track-rating")
    p.add_argument("--id", required=True)
    p.add_argument("--track-no", type=int, required=True)
    p.add_argument("--rating", type=float, required=True)
    p.set_defaults(func=cmd_set_track_rating)

    p = sub.add_parser("set-stage")
    p.add_argument("--id", required=True)
    p.add_argument("--to", required=True)
    p.add_argument("--note")
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=cmd_set_stage)

    p = sub.add_parser("list")
    p.add_argument("--stage")
    p.add_argument("--artist")
    p.add_argument("--tag")
    p.add_argument("--limit", type=int, default=20)
    p.set_defaults(func=cmd_list)

    p = sub.add_parser("find")
    p.add_argument("--query", required=True)
    p.set_defaults(func=cmd_find)

    p = sub.add_parser("stats")
    p.add_argument("--id", required=True)
    p.set_defaults(func=cmd_stats)

    p = sub.add_parser("export")
    p.add_argument("--format", choices=["csv", "json", "md"], required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--fields")
    p.add_argument("--template")
    p.add_argument("--id")
    p.set_defaults(func=cmd_export)

    p = sub.add_parser("snapshot")
    p.set_defaults(func=cmd_snapshot)

    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
