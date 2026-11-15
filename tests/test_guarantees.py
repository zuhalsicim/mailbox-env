"""Every instance keeps the guarantees and follows the dial of its level."""

import dataclasses
import random
from datetime import date, datetime

from mailgen import catalogue
from mailgen.model import Process, Step
from mailgen.policies import thread_start
from mailgen.sampler import DIAL, broken_guarantees, differ, office_hours, sample_instance, share_a_process
from mailgen.truth import build_truth


def test_no_guarantee_is_broken(instance):
    assert broken_guarantees(instance) == []


def test_no_process_holds_more_than_half_of_the_emails(instance):
    truth = build_truth(instance.emails)
    for process in truth["processes"].values():
        assert 2 * len(process["emails"]) <= len(instance.emails)


def test_every_chosen_process_occurs_with_at_least_two_cases(instance):
    for process in instance.processes:
        assert len([case for case in instance.cases if case.process == process.id]) >= 2


def test_size_follows_the_dial(instance):
    dial = DIAL[instance.level]
    assert len(instance.processes) == dial.processes
    assert dial.emails - 2 <= len(instance.emails) <= dial.emails * 1.25
    noise = len([mail for mail in instance.emails if mail.noise])
    assert abs(noise / len(instance.emails) - dial.noise) < 0.03


def test_lookalike_pairs_follow_the_dial(instance):
    dial = DIAL[instance.level]
    fewest, most = dial.lookalike_pairs
    assert fewest <= len(instance.lookalikes) <= most
    assert not dial.triple or share_a_process(instance.lookalikes)
    ids = [process.id for process in instance.processes]
    related = [pair for pair in catalogue.LOOKALIKES if pair[0] in ids and pair[1] in ids]
    assert all(pair in related for pair in instance.lookalikes)
    if most == 0:
        assert related == []


def test_twin_cases_share_people(instance):
    twins = [case for case in instance.cases if case.twin]
    assert bool(twins) == bool(instance.lookalikes)
    for case in twins:
        pair = (case.process, case.twin.process)
        assert pair in instance.lookalikes or pair[::-1] in instance.lookalikes
        assert set(case.people.values()) & set(case.twin.people.values())


def test_times_in_a_case_only_go_forward(instance):
    for case in instance.cases:
        times = [mail.sent for mail in sorted(instance.emails, key=lambda mail: mail.sent) if mail.case is case]
        assert len(times) == len(case.path)
        assert all(earlier < later for earlier, later in zip(times, times[1:]))


def test_a_mail_without_reference_hangs_on_an_older_mail_of_its_case(instance):
    for mail in instance.emails:
        if mail.case and not mail.shows_reference:
            old = mail.answers or mail.forwards
            assert old is not None and old.case is mail.case


def test_nobody_writes_to_themselves(instance):
    assert all(mail.sender != mail.recipient for mail in instance.emails)


def test_ids_are_unique_and_neutral(instance):
    ids = [mail.id for mail in instance.emails]
    assert ids == [f"m{position:04d}" for position in range(1, len(ids) + 1)]
    assert len({mail.message_id for mail in instance.emails}) == len(ids)


def test_level_1_takes_no_help_away():
    for seed in range(1, 6):
        instance = sample_instance(1, seed)
        for mail in instance.emails:
            keyword = next(step.keyword for step in catalogue.STEP_TYPES if step.name == mail.step)
            assert mail.case and not mail.forwards
            assert keyword in mail.subject and keyword in mail.text
            assert mail.case.reference in mail.subject and mail.case.reference in mail.text
        for case in instance.cases:
            threads = {thread_start(mail) for mail in instance.emails if mail.case is case}
            assert len(threads) == 1
        people = {}
        for case in instance.cases:
            for person in case.people.values():
                people.setdefault(person, set()).add(case.process)
        assert all(len(processes) == 1 for processes in people.values())


def test_level_3_takes_help_away():
    for seed in range(1, 6):
        instance = sample_instance(3, seed)
        mails = [mail for mail in instance.emails if mail.case]
        assert any(not mail.names_step for mail in mails)
        assert any(not mail.uses_keyword for mail in mails)
        assert any(mail.case.reference not in mail.text for mail in mails)
        assert any(mail.forwards for mail in mails)
        assert any(mail.answers and mail.answers.case is not mail.case for mail in mails)
        threads_of_case = {}
        for mail in mails:
            threads_of_case.setdefault(mail.case.id, set()).add(thread_start(mail))
        assert any(len(threads) > 1 for threads in threads_of_case.values())
        people = {}
        for case in instance.cases:
            for person in case.people.values():
                people.setdefault(person, set()).add(case.process)
        assert any(len(processes) > 1 for processes in people.values())


def test_processes_with_the_same_roles_order_and_things_do_not_differ():
    one = Process("X1", "one", "", (Step("A", "r", "s", then=("B",)), Step("B", "s", "r")), "Waren", "{thing}", "N-{number}")
    same = dataclasses.replace(one, id="X2", name="two")
    other_order = dataclasses.replace(one, id="X3", steps=(Step("B", "s", "r", then=("A",)), Step("A", "r", "s")))
    other_things = dataclasses.replace(one, id="X4", things="Reisen")
    assert not differ(one, same)
    assert differ(one, other_order)
    assert differ(one, other_things)


def test_office_hours_moves_nights_and_weekends_into_the_next_working_day():
    rng = random.Random(1)
    after_friday_evening = office_hours(datetime(2025, 3, 7, 18, 30), rng)
    assert after_friday_evening.date() == date(2025, 3, 10) and 8 <= after_friday_evening.hour < 17
    after_monday_night = office_hours(datetime(2025, 3, 10, 5, 0), rng)
    assert after_monday_night.date() == date(2025, 3, 10) and 8 <= after_monday_night.hour < 17
    monday_noon = datetime(2025, 3, 10, 12, 15)
    assert office_hours(monday_noon, rng) == monday_noon


def test_mails_of_a_case_are_sent_while_the_office_is_open(instance):
    for mail in instance.emails:
        if mail.case:
            assert mail.sent.weekday() < 5 and 8 <= mail.sent.hour < 17
