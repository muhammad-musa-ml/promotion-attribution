from collections import defaultdict
from dataclasses import dataclass

from .events import DAY, TOUCH_TYPES

CLICK_WINDOW = 7 * DAY
VIEW_WINDOW = DAY


@dataclass(frozen=True)
class Credit:
    user_id: str
    job_id: str
    promo_id: str
    kind: str  # "click", "view" or "period"
    apply_event_id: str


@dataclass(frozen=True)
class Result:
    credits: list
    repeats: int  # events whose id was already seen
    conflicts: int  # repeats whose content differed


def _sort_key(e):
    return (e.ts, e.type, e.user_id, e.promo_id, e.job_id, e.surface, e.event_id)


def dedupe(events):
    """One event per event_id, whatever the arrival order.

    A client retry repeats an event with the same id. If the copies differ,
    the one that sorts first is kept, so the choice does not depend on which
    copy arrived first.
    """
    seen = {}
    repeats = conflicts = 0
    for e in events:
        old = seen.get(e.event_id)
        if old is None:
            seen[e.event_id] = e
            continue
        repeats += 1
        if old != e:
            conflicts += 1
            seen[e.event_id] = min(old, e, key=_sort_key)
    return list(seen.values()), repeats, conflicts


def attribute(events, promos, click_window=CLICK_WINDOW, view_window=VIEW_WINDOW):
    """Credit each applicant to at most one promotion.

    An application is credited to a promotion of the same job when the same
    user clicked it at most click_window before applying, or else saw it at
    most view_window before applying. The touch must fall inside the
    promotion's [start, end) and must not come after the application. The
    latest click wins over any impression, and the latest of its kind wins.
    A user who applies to a job twice counts once, at the first application.
    The result does not depend on arrival order or on repeated events.
    """
    unique, repeats, conflicts = dedupe(events)
    promo_by_id = {p.promo_id: p for p in promos}
    touches = defaultdict(list)
    applies = {}
    for e in sorted(unique, key=lambda e: (e.ts, e.event_id)):
        if e.type == "apply":
            applies.setdefault((e.user_id, e.job_id), e)
            continue
        promo = promo_by_id.get(e.promo_id)
        if promo and promo.start <= e.ts < promo.end:
            touches[(e.user_id, promo.job_id)].append(e)

    credits = []
    for (user, job), apply in applies.items():
        latest = dict.fromkeys(TOUCH_TYPES)
        for t in touches.get((user, job), ()):
            if t.ts > apply.ts:
                break
            limit = click_window if t.type == "click" else view_window
            if apply.ts - t.ts <= limit:
                latest[t.type] = t
        for kind, touch_type in (("click", "click"), ("view", "impression")):
            t = latest[touch_type]
            if t is not None:
                credits.append(Credit(user, job, t.promo_id, kind, apply.event_id))
                break
    credits.sort(key=lambda c: (c.user_id, c.job_id))
    return Result(credits, repeats, conflicts)
