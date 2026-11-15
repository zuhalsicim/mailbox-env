"""The reference answer earns 1 and every shortcut earns 0, on every instance of the batch."""

from datetime import datetime, timedelta

import pytest

from mailgen.grade import grade
from mailgen.model import Email, Person
from mailgen.policies import (
    SHORTCUTS,
    bare_subject,
    by_keyword,
    grouped,
    keyword_step,
    reference,
    sender_pair,
    thread_start,
)
from mailgen.truth import build_truth

ANNA = Person("Anna Beispiel", "anna@firma.example")
BERT = Person("Bert Beispiel", "bert@firma.example")
MONDAY = datetime(2025, 3, 3, 9, 0)


def test_reference_earns_1(instance):
    assert grade(reference(instance), build_truth(instance.emails))["reward"] == 1


@pytest.mark.parametrize("name", SHORTCUTS)
def test_shortcut_earns_0(instance, name):
    assert grade(SHORTCUTS[name](instance), build_truth(instance.emails))["reward"] == 0


def test_keyword_lookup_fails_on_the_flow_alone(instance):
    """It is given the true cases, so every email is in the right place; only the looked-up steps are wrong."""
    result = grade(by_keyword(instance), build_truth(instance.emails))
    assert result["noise_exact"]
    assert all(process["emails_exact"] for process in result["processes"].values())
    assert not all(process["flow_exact"] for process in result["processes"].values())


def test_every_shortcut_answer_has_the_form_of_an_answer(instance):
    truth = build_truth(instance.emails)
    for name, shortcut in SHORTCUTS.items():
        if name != "no_op":
            assert "processes" in grade(shortcut(instance), truth), name


def test_bare_subject_drops_the_marks_of_answers_and_forwards():
    assert bare_subject("AW: WG: Rechnung B-12345") == "rechnung b-12345"
    assert bare_subject("Rechnung B-12345") == "rechnung b-12345"


def test_keyword_step_takes_the_first_word_of_the_glossary_it_finds():
    mail = Email(ANNA, BERT, MONDAY, subject="Zahlung", body="die Zahlung zur Rechnung ist raus")
    assert keyword_step(mail) == "RECHNUNG"  # RECHNUNG stands before ZAHLUNG in the glossary
    assert keyword_step(Email(ANNA, BERT, MONDAY, subject="Hallo", body="bis morgen")) is None


def test_sender_pair_ignores_the_direction():
    assert sender_pair(Email(ANNA, BERT, MONDAY)) == sender_pair(Email(BERT, ANNA, MONDAY))


def test_thread_start_follows_answers_but_not_forwards():
    first = Email(ANNA, BERT, MONDAY, id="m1")
    answer = Email(BERT, ANNA, MONDAY + timedelta(hours=1), id="m2", answers=first)
    second_answer = Email(ANNA, BERT, MONDAY + timedelta(hours=2), id="m3", answers=answer)
    forward = Email(ANNA, BERT, MONDAY + timedelta(hours=3), id="m4", forwards=second_answer)
    assert [thread_start(mail) for mail in (first, answer, second_answer, forward)] == ["m1", "m1", "m1", "m4"]


def test_grouped_keeps_the_mails_of_one_key_together():
    mails = [Email(ANNA, BERT, MONDAY, id="m1"), Email(BERT, ANNA, MONDAY, id="m2"), Email(ANNA, BERT, MONDAY, id="m3")]
    groups = grouped(mails, lambda mail: mail.sender.name)
    assert [[mail.id for mail in group] for group in groups] == [["m1", "m3"], ["m2"]]
