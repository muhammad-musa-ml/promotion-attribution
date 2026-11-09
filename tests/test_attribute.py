import random

from promoattr.attribute import attribute, dedupe
from promoattr.events import DAY, HOUR, Event, Promotion

PROMOS = [Promotion("p1", "j1", 0, 10 * DAY), Promotion("p2", "j2", 0, 10 * DAY)]


def imp(eid, user, ts, promo="p1"):
    return Event(eid, "impression", user, ts, promo_id=promo, surface="feed")


def clk(eid, user, ts, promo="p1"):
    return Event(eid, "click", user, ts, promo_id=promo, surface="feed")


def app(eid, user, ts, job="j1"):
    return Event(eid, "apply", user, ts, job_id=job)


def credited(events, **kw):
    r = attribute(events, PROMOS, **kw)
    return [(c.user_id, c.job_id, c.promo_id, c.kind) for c in r.credits]


def test_hand_computed_case():
    events = [
        clk("c1", "ann", 1 * DAY),
        app("a1", "ann", 1 * DAY + 2 * HOUR),  # click, then apply: click credit
        imp("i1", "bob", 2 * DAY),
        app("a2", "bob", 2 * DAY + 5 * HOUR),  # view only: view credit
        app("a3", "cat", 3 * DAY),  # no touch: organic
        imp("i2", "dan", 2 * DAY),
        app("a4", "dan", 2 * DAY + 2 * DAY),  # view too old: organic
    ]
    assert credited(events) == [
        ("ann", "j1", "p1", "click"),
        ("bob", "j1", "p1", "view"),
    ]


def test_window_edges_are_inclusive():
    on_edge = [clk("c", "u", 0), app("a", "u", 7 * DAY)]
    past_edge = [clk("c", "u", 0), app("a", "u", 7 * DAY + 1)]
    assert credited(on_edge) == [("u", "j1", "p1", "click")]
    assert credited(past_edge) == []
    view_edge = [imp("i", "u", 0), app("a", "u", DAY)]
    assert credited(view_edge) == [("u", "j1", "p1", "view")]
    assert credited([imp("i", "u", 0), app("a", "u", DAY + 1)]) == []


def test_touch_after_the_application_is_not_credited():
    assert credited([app("a", "u", 100), clk("c", "u", 101)]) == []


def test_touch_outside_the_promotion_is_not_credited():
    late_promo = [Promotion("p1", "j1", 5 * DAY, 8 * DAY)]
    before = [clk("c", "u", 4 * DAY), app("a", "u", 5 * DAY + 1)]
    at_end = [clk("c", "u", 8 * DAY), app("a", "u", 8 * DAY + 1)]
    for events in (before, at_end):
        assert attribute(events, late_promo).credits == []


def test_touch_for_another_job_is_not_credited():
    events = [clk("c", "u", 0, promo="p2"), app("a", "u", HOUR, job="j1")]
    assert credited(events) == []


def test_click_beats_a_later_impression():
    events = [clk("c", "u", 0), imp("i", "u", 6 * DAY), app("a", "u", 6 * DAY + HOUR)]
    assert credited(events) == [("u", "j1", "p1", "click")]


def test_two_applications_to_one_job_credit_once():
    events = [clk("c", "u", 0), app("a1", "u", HOUR), app("a2", "u", 2 * HOUR)]
    r = attribute(events, PROMOS)
    assert [c.apply_event_id for c in r.credits] == ["a1"]


def test_repeated_event_ids_are_counted_once():
    events = [clk("c", "u", 0), clk("c", "u", 0), app("a", "u", HOUR), app("a", "u", HOUR)]
    r = attribute(events, PROMOS)
    assert len(r.credits) == 1
    assert (r.repeats, r.conflicts) == (2, 0)


def test_conflicting_copies_resolve_the_same_way_in_both_orders():
    early, late = clk("c", "u", 0), clk("c", "u", 5 * DAY)
    assert dedupe([early, late])[0] == dedupe([late, early])[0] == [early]
    assert dedupe([early, late])[2] == 1


def test_arrival_order_does_not_change_the_result():
    rng = random.Random(3)
    events = []
    for n in range(40):
        user = f"u{n}"
        events += [imp(f"i{n}", user, n * HOUR), clk(f"c{n}", user, n * HOUR + 60)]
        events.append(app(f"a{n}", user, n * HOUR + rng.randint(0, 9 * DAY)))
    events += rng.sample(events, 15)  # client retries
    expected = attribute(events, PROMOS).credits
    for _ in range(25):
        rng.shuffle(events)
        assert attribute(events, PROMOS).credits == expected
