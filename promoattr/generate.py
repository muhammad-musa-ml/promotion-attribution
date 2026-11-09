import random
from dataclasses import dataclass

from .events import DAY, HOUR, Event, Promotion

SURFACES = ("search", "feed", "digest", "inbox", "message")

# What a user who considers a promoted job does, with the cause set here.
# (name, probability, applies because of the promotion)
SCENARIOS = (
    ("click_then_apply", 0.06, True),
    ("view_then_apply", 0.03, True),
    ("view_then_apply_anyway", 0.12, False),
    ("old_click_then_apply", 0.04, False),
    ("view_only", 0.30, False),
    ("apply_without_touch", 0.10, False),
)

DUPLICATE_RATE = 0.08  # share of events sent twice by a client retry
LATE_RATE = 0.12  # share of events that reach the log up to three days late


@dataclass
class Dataset:
    events: list  # in arrival order
    promos: list
    caused: set  # (user_id, job_id) pairs that applied because of the promotion


def generate(seed, users=2000, jobs=30, promoted=10, considered=3):
    rng = random.Random(seed)
    promos = []
    for i, j in enumerate(rng.sample(range(jobs), promoted)):
        start = rng.randint(5, 30) * DAY
        promos.append(Promotion(f"p{i}", f"j{j}", start, start + rng.randint(14, 21) * DAY))
    promo_by_job = {p.job_id: p for p in promos}

    events, caused = [], set()
    counter = iter(range(10**9))

    def add(kind, user, ts, **kw):
        events.append(Event(f"e{next(counter)}", kind, user, int(ts), **kw))

    def touch(kind, user, promo, ts):
        add(kind, user, ts, promo_id=promo.promo_id, surface=rng.choice(SURFACES))

    for u in range(users):
        user = f"u{u}"
        for j in rng.sample(range(jobs), considered):
            job = f"j{j}"
            promo = promo_by_job.get(job)
            if promo is None:
                if rng.random() < 0.15:
                    add("apply", user, rng.uniform(0, 60 * DAY), job_id=job)
                continue
            r, scenario = rng.random(), None
            for name, p, cause in SCENARIOS:
                if r < p:
                    scenario = (name, cause)
                    break
                r -= p
            if scenario is None:
                continue
            name, cause = scenario
            t = rng.uniform(promo.start, promo.end - 1)
            if name == "click_then_apply":
                if rng.random() < 0.6:
                    touch("impression", user, promo, max(promo.start, t - rng.uniform(60, 1800)))
                touch("click", user, promo, t)
                add("apply", user, t + min(rng.expovariate(1 / (8 * HOUR)), 6 * DAY), job_id=job)
            elif name == "view_then_apply":
                touch("impression", user, promo, t)
                add("apply", user, t + rng.uniform(HOUR, 20 * HOUR), job_id=job)
            elif name == "view_then_apply_anyway":
                touch("impression", user, promo, t)
                add("apply", user, t + rng.uniform(0, 72 * HOUR), job_id=job)
            elif name == "old_click_then_apply":
                touch("click", user, promo, t)
                add("apply", user, t + rng.uniform(8 * DAY, 20 * DAY), job_id=job)
            elif name == "view_only":
                touch("impression", user, promo, t)
            else:
                add("apply", user, rng.uniform(promo.start, promo.end - 1), job_id=job)
            if cause:
                caused.add((user, job))

    return Dataset(_deliver(events, rng), promos, caused)


def _deliver(events, rng):
    """Order the log the way a client pipeline would hand it over."""
    sent = []
    for e in events:
        arrival = e.ts + (rng.uniform(0, 3 * DAY) if rng.random() < LATE_RATE else 0)
        sent.append((arrival, rng.random(), e))
        if rng.random() < DUPLICATE_RATE:
            sent.append((arrival + rng.uniform(0, 60), rng.random(), e))
    sent.sort(key=lambda x: (x[0], x[1]))
    return [e for _, _, e in sent]
