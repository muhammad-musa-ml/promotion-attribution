from promoattr.attribute import Credit
from promoattr.evaluate import RULE, run_seed, score, write_results, run_seeds

CAUSED = {("a", "j1"), ("b", "j1"), ("c", "j1"), ("d", "j1")}


def credit(user, apply_id="x"):
    return Credit(user, "j1", "p1", "click", apply_id)


def test_score_by_hand():
    credits = [credit("a"), credit("b"), credit("z"), credit("z", "y")]
    s = score(credits, CAUSED)
    assert (s["credited"], s["correct"], s["caused"]) == (4, 2, 4)
    assert s["precision"] == 0.5 and s["recall"] == 0.5


def test_a_repeated_credit_lowers_precision_but_not_recall():
    s = score([credit("a"), credit("a", "y"), credit("b")], CAUSED)
    assert s["credited"] == 3 and s["precision"] == 1.0 and s["recall"] == 0.5


def test_nothing_credited_has_no_precision():
    s = score([], CAUSED)
    assert s["precision"] is None and s["recall"] == 0.0


def test_on_a_generated_log_the_rule_beats_each_baseline_where_it_is_weak():
    _, rows = run_seed(3, users=600, jobs=20, promoted=6)
    assert rows[RULE]["precision"] > rows["period share"]["precision"]
    assert rows[RULE]["recall"] > rows["windows in arrival order (click 7d, view 24h)"]["recall"]


def test_results_files_are_written(tmp_path):
    gen = dict(users=200, jobs=10, promoted=3, considered=3)
    runs = run_seeds([1, 2], **gen)
    write_results(runs, gen, tmp_path)
    assert (tmp_path / "summary.md").read_text().startswith("# Results")
    rows = (tmp_path / "by_seed.csv").read_text().splitlines()
    assert rows[0].startswith("seed,method")
    assert len(rows) == 1 + 2 * 7  # period, arrival order, five view windows
