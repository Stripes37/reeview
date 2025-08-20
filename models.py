from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import List, Optional, Any
from datetime import datetime

ISO_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


class Stage(str, Enum):
    IDEATION = "IDEATION"
    SCRIPTED = "SCRIPTED"
    GRAPHICS_READY = "GRAPHICS_READY"
    VO_READY = "VO_READY"
    EDITING = "EDITING"
    SCHEDULED = "SCHEDULED"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


ALLOWED_TRANSITIONS = {
    Stage.IDEATION: {Stage.SCRIPTED},
    Stage.SCRIPTED: {Stage.GRAPHICS_READY, Stage.IDEATION},
    Stage.GRAPHICS_READY: {Stage.VO_READY, Stage.SCRIPTED},
    Stage.VO_READY: {Stage.EDITING, Stage.GRAPHICS_READY},
    Stage.EDITING: {Stage.SCHEDULED, Stage.VO_READY},
    Stage.SCHEDULED: {Stage.PUBLISHED, Stage.EDITING},
    Stage.PUBLISHED: {Stage.ARCHIVED},
    Stage.ARCHIVED: set(),
}


@dataclass
class Track:
    track_no: int
    title: str
    rating: Optional[float] = None
    duration_sec: Optional[int] = None


@dataclass
class BestProduction:
    track: str
    producer: List[str]


@dataclass
class BestFeature:
    artist: str
    track: str


@dataclass
class Transition:
    from_stage: Optional[Stage]
    to_stage: Stage
    at: str
    note: str = ""


@dataclass
class Status:
    stage: Stage = Stage.IDEATION
    history: List[Transition] = field(default_factory=list)

    def transition(self, to: Stage, note: str = "", force: bool = False) -> bool:
        allowed = ALLOWED_TRANSITIONS.get(self.stage, set())
        if to not in allowed and not force:
            raise ValueError(f"Invalid transition {self.stage} -> {to}")
        self.history.append(
            Transition(from_stage=self.stage, to_stage=to, at=datetime.utcnow().strftime(ISO_FORMAT), note=note)
        )
        self.stage = to
        return True


@dataclass
class Album:
    id: str
    artist: str
    album: str
    release_date: Optional[str] = None
    genre: List[str] = field(default_factory=list)
    cover_image_path: Optional[str] = None
    links: dict = field(default_factory=dict)
    tracklist: List[Track] = field(default_factory=list)
    favourite_song: Optional[str] = None
    least_favourite_song: Optional[str] = None
    best_moment: Optional[str] = None
    best_production: Optional[BestProduction] = None
    best_feature: Optional[BestFeature] = None
    final_score: Optional[float] = None
    review_notes: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    status: Status = field(default_factory=Status)
    timing: dict = field(default_factory=dict)
    assets: dict = field(default_factory=dict)
    audit: dict = field(default_factory=dict)

    def validate(self) -> List[str]:
        warnings: List[str] = []
        if self.final_score is not None and not (0 <= self.final_score <= 10):
            warnings.append("final_score out of range")
        for t in self.tracklist:
            if t.rating is not None and not (0 <= t.rating <= 10):
                warnings.append(f"track {t.track_no} rating out of range")
        return warnings

    def average_track_rating(self) -> Optional[float]:
        ratings = [t.rating for t in self.tracklist if t.rating is not None]
        if not ratings:
            return None
        return sum(ratings) / len(ratings)

    def top_track(self) -> Optional[Track]:
        rated = [t for t in self.tracklist if t.rating is not None]
        return max(rated, key=lambda t: t.rating) if rated else None

    def low_track(self) -> Optional[Track]:
        rated = [t for t in self.tracklist if t.rating is not None]
        return min(rated, key=lambda t: t.rating) if rated else None

    def to_dict(self) -> dict:
        def convert(value: Any) -> Any:
            if dataclass_is_instance := hasattr(value, "__dataclass_fields__"):
                return {k: convert(v) for k, v in asdict(value).items()}
            if isinstance(value, list):
                return [convert(v) for v in value]
            return value

        return convert(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Album":
        tracklist = [Track(**t) for t in data.get("tracklist", [])]
        bp = data.get("best_production")
        bf = data.get("best_feature")
        status = data.get("status") or {}
        history = [
            Transition(
                from_stage=Stage(h.get("from_stage")) if h.get("from_stage") else None,
                to_stage=Stage(h["to_stage"]),
                at=h["at"],
                note=h.get("note", ""),
            )
            for h in status.get("history", [])
        ]
        status_obj = Status(stage=Stage(status.get("stage", "IDEATION")), history=history)
        return cls(
            id=data["id"],
            artist=data.get("artist", ""),
            album=data.get("album", ""),
            release_date=data.get("release_date"),
            genre=data.get("genre", []),
            cover_image_path=data.get("cover_image_path"),
            links=data.get("links", {}),
            tracklist=tracklist,
            favourite_song=data.get("favourite_song"),
            least_favourite_song=data.get("least_favourite_song"),
            best_moment=data.get("best_moment"),
            best_production=BestProduction(**bp) if bp else None,
            best_feature=BestFeature(**bf) if bf else None,
            final_score=data.get("final_score"),
            review_notes=data.get("review_notes"),
            tags=data.get("tags", []),
            status=status_obj,
            timing=data.get("timing", {}),
            assets=data.get("assets", {}),
            audit=data.get("audit", {}),
        )
