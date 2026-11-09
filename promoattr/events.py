import json
from dataclasses import asdict, dataclass

HOUR = 3600
DAY = 24 * HOUR

TOUCH_TYPES = ("impression", "click")
EVENT_TYPES = TOUCH_TYPES + ("apply",)


@dataclass(frozen=True)
class Event:
    """One logged event. ts is seconds since the start of the log.

    Impressions and clicks name the promotion they belong to. Applications
    name the job.
    """

    event_id: str
    type: str
    user_id: str
    ts: int
    promo_id: str = ""
    job_id: str = ""
    surface: str = ""

    def __post_init__(self):
        if self.type not in EVENT_TYPES:
            raise ValueError(f"unknown event type {self.type!r}")
        if self.type in TOUCH_TYPES and not self.promo_id:
            raise ValueError(f"{self.type} {self.event_id} has no promo_id")
        if self.type == "apply" and not self.job_id:
            raise ValueError(f"apply {self.event_id} has no job_id")


@dataclass(frozen=True)
class Promotion:
    promo_id: str
    job_id: str
    start: int
    end: int  # exclusive


def dump_events(events, path):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        for e in events:
            f.write(json.dumps(asdict(e), sort_keys=True) + "\n")


def load_events(path):
    events = []
    with open(path, encoding="utf-8") as f:
        for n, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                events.append(Event(**json.loads(line)))
            except (TypeError, ValueError) as err:
                raise ValueError(f"{path}:{n}: {err}") from err
    return events
