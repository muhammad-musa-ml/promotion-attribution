from promoattr.attribute import attribute
from promoattr.baselines import arrival_order, period_share
from promoattr.events import DAY, HOUR, Event, Promotion

PROMOS = [Promotion("p1", "j1", 0, 10 * DAY)]


def clk(eid, user, ts):
    return Event(eid, "click", user, ts, promo_id="p1", surface="feed")


def app(eid, user, ts):
    return Event(eid, "apply", user, ts, job_id="j1")


def test_period_share_credits_an_applicant_with_no_touch():
    events = [app("a", "u", DAY)]
    assert len(period_share(events, PROMOS)) == 1
    assert attribute(events, PROMOS).credits == []


def test_period_share_ignores_applications_outside_the_promotion():
    assert period_share([app("a", "u", 10 * DAY)], PROMOS) == []


def test_arrival_order_misses_a_click_that_arrives_after_the_application():
    events = [app("a", "u", HOUR), clk("c", "u", 0)]  # the click was delayed
    assert arrival_order(events, PROMOS) == []
    assert len(attribute(events, PROMOS).credits) == 1


def test_arrival_order_credits_a_repeated_application_twice():
    events = [clk("c", "u", 0), app("a", "u", HOUR), app("a", "u", HOUR)]
    assert len(arrival_order(events, PROMOS)) == 2
    assert len(attribute(events, PROMOS).credits) == 1


def test_arrival_order_lets_a_late_older_click_replace_a_newer_one():
    events = [clk("new", "u", 6 * DAY), clk("old", "u", 0), app("a", "u", 7 * DAY + HOUR)]
    assert arrival_order(events, PROMOS) == []
    assert len(attribute(events, PROMOS).credits) == 1


def test_arrival_order_does_not_credit_a_touch_dated_after_the_application():
    events = [clk("c", "u", 2 * HOUR), app("a", "u", HOUR)]
    assert arrival_order(events, PROMOS) == []


def test_arrival_order_agrees_when_the_log_is_clean_and_in_order():
    events = [clk("c", "u", 0), app("a", "u", HOUR)]
    assert [(c.user_id, c.kind) for c in arrival_order(events, PROMOS)] == [("u", "click")]
