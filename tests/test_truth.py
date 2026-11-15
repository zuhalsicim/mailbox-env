"""The truth and the directly-follows graph, on a log small enough to check by hand."""

from datetime import datetime, timedelta

import pytest

from mailgen.model import Case, Email, Person
from mailgen.truth import build_truth, directly_follows

ANNA = Person("Anna Beispiel", "anna@firma.example")
BERT = Person("Bert Beispiel", "bert@firma.example")
MONDAY = datetime(2025, 3, 3, 9, 0)


def mail(mail_id, hour, case=None, step=None):
    return Email(ANNA, BERT, MONDAY + timedelta(hours=hour), case=case, step=step, id=mail_id)


def hand_built_log():
    """Two cases of process P1 and one of P2, their mails mixed in time, and one mail of no process."""
    first = Case("case-1", "P1")
    second = Case("case-2", "P1")
    third = Case("case-3", "P2")
    return [
        mail("m1", 1, first, "A"),
        mail("m2", 2, second, "A"),
        mail("m3", 3, first, "B"),
        mail("m4", 4, third, "B"),
        mail("m5", 5, second, "C"),
        mail("m6", 6, first, "C"),
        mail("m7", 7, third, "A"),
        mail("m8", 8),
    ]


def test_directly_follows_takes_neighbours_only():
    assert directly_follows([["A", "B", "C"]]) == [["A", "B"], ["B", "C"]]


def test_directly_follows_joins_traces_and_keeps_each_pair_once():
    assert directly_follows([["A", "B"], ["A", "B", "A"], ["C"]]) == [["A", "B"], ["B", "A"]]


def test_directly_follows_of_nothing_is_empty():
    assert directly_follows([]) == []
    assert directly_follows([["A"]]) == []


def test_flow_is_taken_per_case_not_across_cases():
    truth = build_truth(hand_built_log())
    # case-1 runs A, B, C and case-2 runs A, C. Read as one stream, P1 would also show (A, A) and (C, C).
    assert truth["processes"]["P1"]["flow"] == [["A", "B"], ["A", "C"], ["B", "C"]]
    assert truth["processes"]["P2"]["flow"] == [["B", "A"]]


def test_emails_of_each_process_and_noise():
    truth = build_truth(hand_built_log())
    assert truth["processes"]["P1"]["emails"] == ["m1", "m2", "m3", "m5", "m6"]
    assert truth["processes"]["P2"]["emails"] == ["m4", "m7"]
    assert truth["noise"] == ["m8"]


def test_every_email_has_its_case_process_and_step():
    truth = build_truth(hand_built_log())
    assert truth["emails"]["m3"] == {"case": "case-1", "process": "P1", "step": "B"}
    assert truth["emails"]["m8"] == {"case": None, "process": None, "step": None}
    assert len(truth["emails"]) == 8


def test_order_comes_from_the_time_not_from_the_list():
    log = hand_built_log()
    assert build_truth(list(reversed(log))) == build_truth(log)


def test_two_mails_of_a_case_at_the_same_moment_are_refused():
    case = Case("case-1", "P1")
    with pytest.raises(ValueError):
        build_truth([mail("m1", 1, case, "A"), mail("m2", 1, case, "B")])
