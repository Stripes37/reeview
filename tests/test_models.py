import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from models import Album, Track, Status, Stage
import pytest


def test_status_transition():
    s = Status()
    s.transition(Stage.SCRIPTED)
    assert s.stage == Stage.SCRIPTED
    with pytest.raises(ValueError):
        s.transition(Stage.PUBLISHED)


def test_album_average_and_top_low():
    album = Album(
        id="1",
        artist="Artist",
        album="Album",
        tracklist=[Track(track_no=1, title="A", rating=5.0), Track(track_no=2, title="B", rating=7.0)],
    )
    assert album.average_track_rating() == 6.0
    assert album.top_track().title == "B"
    assert album.low_track().title == "A"
