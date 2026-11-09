import pytest

from promoattr.events import Event, dump_events, load_events


def test_round_trip(tmp_path):
    events = [
        Event("e1", "impression", "u1", 10, promo_id="p1", surface="feed"),
        Event("e2", "click", "u1", 20, promo_id="p1", surface="feed"),
        Event("e3", "apply", "u1", 30, job_id="j1"),
    ]
    path = tmp_path / "events.jsonl"
    dump_events(events, path)
    assert load_events(path) == events


def test_touch_without_promotion_is_rejected():
    with pytest.raises(ValueError):
        Event("e1", "click", "u1", 10)


def test_apply_without_job_is_rejected():
    with pytest.raises(ValueError):
        Event("e1", "apply", "u1", 10)


def test_unknown_type_is_rejected():
    with pytest.raises(ValueError):
        Event("e1", "view", "u1", 10, promo_id="p1")


def test_bad_line_names_the_line(tmp_path):
    path = tmp_path / "events.jsonl"
    path.write_text('{"event_id": "e1", "type": "apply", "user_id": "u1", "ts": 1}\n')
    with pytest.raises(ValueError, match=":1:"):
        load_events(path)
