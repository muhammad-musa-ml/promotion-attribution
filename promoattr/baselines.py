from .attribute import CLICK_WINDOW, VIEW_WINDOW, Credit, dedupe


def period_share(events, promos):
    """Credit every applicant who applied to a promoted job while it was promoted.

    No touch is needed. This is the count a dashboard gives when it joins
    applications to promotions on job and date only.
    """
    unique, _, _ = dedupe(events)
    applies = {}
    for e in sorted(unique, key=lambda e: (e.ts, e.event_id)):
        if e.type == "apply":
            applies.setdefault((e.user_id, e.job_id), e)
    credits = []
    for (user, job), a in applies.items():
        for p in promos:
            if p.job_id == job and p.start <= a.ts < p.end:
                credits.append(Credit(user, job, p.promo_id, "period", a.event_id))
                break
    credits.sort(key=lambda c: (c.user_id, c.job_id))
    return credits


def arrival_order(events, promos, click_window=CLICK_WINDOW, view_window=VIEW_WINDOW):
    """The same click and view windows, applied as events arrive.

    It reads the log once in arrival order, keeps the most recently arrived
    click and impression per user and job, and credits every application
    event when it arrives. A touch that arrives after its application is
    missed, a repeated application is credited twice, and a late copy of an
    older touch replaces a newer one.
    """
    promo_by_id = {p.promo_id: p for p in promos}
    last = {}
    credits = []
    for e in events:
        if e.type != "apply":
            promo = promo_by_id.get(e.promo_id)
            if promo and promo.start <= e.ts < promo.end:
                last[(e.user_id, promo.job_id, e.type)] = e
            continue
        for kind, touch_type, limit in (
            ("click", "click", click_window),
            ("view", "impression", view_window),
        ):
            t = last.get((e.user_id, e.job_id, touch_type))
            if t is not None and 0 <= e.ts - t.ts <= limit:
                credits.append(Credit(e.user_id, e.job_id, t.promo_id, kind, e.event_id))
                break
    credits.sort(key=lambda c: (c.user_id, c.job_id, c.apply_event_id))
    return credits
