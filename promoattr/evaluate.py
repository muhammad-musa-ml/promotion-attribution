import csv
import os
from statistics import mean

from .attribute import CLICK_WINDOW, attribute
from .baselines import arrival_order, period_share
from .events import DAY, HOUR
from .generate import generate

OFF = -1  # a view window nothing can fall inside

VIEW_SWEEP = (
    ("off", OFF),
    ("1h", HOUR),
    ("6h", 6 * HOUR),
    ("24h", DAY),
    ("72h", 3 * DAY),
)

PERIOD = "period share"
ARRIVAL = "windows in arrival order (click 7d, view 24h)"
RULE = "attribute (click 7d, view 24h)"


def score(credits, caused):
    """Compare credits with the pairs that applied because of the promotion.

    credited counts credit entries, so a repeated application counts twice.
    precision is the share of entries that are caused pairs; recall is the
    share of caused pairs credited at least once.
    """
    entries = len(credits)
    correct = sum((c.user_id, c.job_id) in caused for c in credits)
    covered = len({(c.user_id, c.job_id) for c in credits} & caused)
    return {
        "credited": entries,
        "correct": correct,
        "caused": len(caused),
        "precision": correct / entries if entries else None,
        "recall": covered / len(caused) if caused else None,
    }


def methods_for(dataset):
    events, promos = dataset.events, dataset.promos
    out = {
        PERIOD: period_share(events, promos),
        ARRIVAL: arrival_order(events, promos),
    }
    for label, window in VIEW_SWEEP:
        name = f"attribute (click 7d, view {label})"
        out[name] = attribute(events, promos, CLICK_WINDOW, window).credits
    return out


def run_seed(seed, **gen):
    d = generate(seed, **gen)
    rows = {name: score(credits, d.caused) for name, credits in methods_for(d).items()}
    return d, rows


def run_seeds(seeds, **gen):
    return {seed: run_seed(seed, **gen) for seed in seeds}


def _pct(x):
    return "-" if x is None else f"{100 * x:.1f}%"


def _spread(values):
    values = [v for v in values if v is not None]
    return f"{_pct(mean(values))} ({_pct(min(values))} to {_pct(max(values))})"


def _table(runs, names):
    lines = [
        "| method | credited / caused | precision | recall |",
        "| --- | --- | --- | --- |",
    ]
    for name in names:
        rows = [r[1][name] for r in runs.values()]
        ratio = [r["credited"] / r["caused"] for r in rows]
        lines.append(
            f"| {name} | {mean(ratio):.2f} ({min(ratio):.2f} to {max(ratio):.2f}) "
            f"| {_spread([r['precision'] for r in rows])} "
            f"| {_spread([r['recall'] for r in rows])} |"
        )
    return "\n".join(lines)


def summary(runs, gen):
    datasets = [r[0] for r in runs.values()]
    events = [len(d.events) for d in datasets]
    caused = [len(d.caused) for d in datasets]
    sweep = [f"attribute (click 7d, view {label})" for label, _ in VIEW_SWEEP]
    return "\n".join(
        [
            "# Results",
            "",
            f"Seeds {min(runs)} to {max(runs)}, generator settings {gen}. Each cell is the "
            "mean over seeds with the lowest and highest seed in brackets. "
            f"Events per seed: {min(events)} to {max(events)}. "
            f"Applications caused by a promotion per seed: {min(caused)} to {max(caused)}.",
            "",
            "## Methods",
            "",
            _table(runs, [PERIOD, ARRIVAL, RULE]),
            "",
            "## Length of the view window (click window fixed at 7 days)",
            "",
            _table(runs, sweep),
            "",
            "credited / caused is the number of credit entries divided by the number of "
            "applications the generator made because of a promotion; 1.00 means the right "
            "total, above 1 means the report claims more than the promotions caused.",
            "",
        ]
    )


def write_results(runs, gen, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "by_seed.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["seed", "method", "credited", "correct", "caused", "precision", "recall"])
        for seed, (_, rows) in runs.items():
            for name, r in rows.items():
                w.writerow(
                    [seed, name, r["credited"], r["correct"], r["caused"],
                     "" if r["precision"] is None else f"{r['precision']:.4f}",
                     "" if r["recall"] is None else f"{r['recall']:.4f}"]
                )
    with open(os.path.join(out_dir, "summary.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write(summary(runs, gen))
