import random

from promoattr.attribute import attribute
from promoattr.generate import generate

SMALL = dict(users=300, jobs=12, promoted=4)


def test_same_seed_gives_the_same_log():
    a, b = generate(5, **SMALL), generate(5, **SMALL)
    assert a.events == b.events and a.promos == b.promos and a.caused == b.caused


def test_different_seeds_differ():
    assert generate(5, **SMALL).events != generate(6, **SMALL).events


def test_every_touch_falls_inside_its_promotion():
    d = generate(5, **SMALL)
    promo = {p.promo_id: p for p in d.promos}
    touches = [e for e in d.events if e.type != "apply"]
    assert touches
    assert all(promo[e.promo_id].start <= e.ts < promo[e.promo_id].end for e in touches)


def test_every_caused_pair_has_an_application_to_a_promoted_job():
    d = generate(5, **SMALL)
    applied = {(e.user_id, e.job_id) for e in d.events if e.type == "apply"}
    promoted_jobs = {p.job_id for p in d.promos}
    assert d.caused and d.caused <= applied
    assert all(job in promoted_jobs for _, job in d.caused)


def test_the_log_has_repeats_and_late_events():
    d = generate(5, **SMALL)
    ids = [e.event_id for e in d.events]
    assert len(ids) > len(set(ids))
    assert any(a.ts > b.ts for a, b in zip(d.events, d.events[1:]))


def test_credits_do_not_change_when_the_generated_log_is_reshuffled():
    d = generate(5, **SMALL)
    expected = attribute(d.events, d.promos).credits
    events = list(d.events)
    random.Random(1).shuffle(events)
    assert attribute(events, d.promos).credits == expected
