"""The audit finds what it is there to find. A check that cannot fail proves nothing."""

from datetime import datetime

from mailgen import audit
from mailgen.model import Email, Person
from mailgen.package import build_files
from mailgen.sampler import sample_instance

JANA = Person("Jana Wolff", "jana.wolff@halden-roth.example")
UWE = Person("Uwe Kranz", "uwe.kranz@halden-roth.example")
MONDAY = datetime(2025, 3, 3, 9, 0)


def test_clean_instances_have_no_leak(instance):
    assert audit.leaks(instance, build_files(instance)) == []


def test_small_audit_passes():
    report = audit.run(6)
    assert report["passed"]
    assert report["instances"] == 6
    assert report["leaks"] == [] and report["failures"] == []
    assert report["reference_1"] == 6
    assert all(count == 6 for count in report["shortcut_0"].values())
    assert sorted(report["signatures"]) == [1, 2, 3]
    assert sum(report["signatures"].values()) + report["duplicate_instances"] == 6
    assert "audit passed" in audit.summary(report)


def plant_case_header(instance):
    """The files of an instance, with a header that names the case added to its first mail of a case."""
    files = build_files(instance)
    mail = next(mail for mail in instance.emails if mail.case)
    path = f"environment/mailbox/{mail.id}.eml"
    files[path] = f"X-Case: {mail.case.id}\n" + files[path]
    return files


def test_planted_case_header_is_found():
    instance = sample_instance(2, 1)
    hits = audit.leaks(instance, plant_case_header(instance))
    assert any("unexpected header X-Case" in hit for hit in hits)
    assert any("contains case-" in hit for hit in hits)


def test_planted_case_header_fails_the_audit():
    def files_with_one_leak(instance):
        if (instance.level, instance.seed) == (2, 1):
            return plant_case_header(instance)
        return build_files(instance)

    report = audit.run(6, files_of=files_with_one_leak)
    assert not report["passed"]
    assert report["leaks"] and all(hit.startswith("level 2, seed 1:") for hit in report["leaks"])
    assert "audit FAILED" in audit.summary(report)


def test_a_header_without_any_id_is_still_unexpected():
    instance = sample_instance(1, 1)
    files = build_files(instance)
    files["environment/mailbox/m0001.eml"] = "X-Folder: orders\n" + files["environment/mailbox/m0001.eml"]
    assert audit.leaks(instance, files) == ["environment/mailbox/m0001.eml: unexpected header X-Folder"]


def test_process_id_or_step_name_in_a_mail_is_found():
    instance = sample_instance(1, 1)
    files = build_files(instance)
    files["environment/mailbox/m0001.eml"] += "PS: K01\n"
    files["environment/mailbox/m0002.eml"] += "PS: ANGEBOT\n"
    hits = audit.leaks(instance, files)
    assert "environment/mailbox/m0001.eml: contains K01" in hits
    assert "environment/mailbox/m0002.eml: contains ANGEBOT" in hits


def test_truth_in_the_agents_folder_is_found():
    instance = sample_instance(1, 1)
    files = build_files(instance)
    files["environment/expected.json"] = files["tests/expected.json"]
    hits = audit.leaks(instance, files)
    assert "environment/expected.json: a file the agent should not have" in hits


def test_ids_that_follow_the_truth_are_found():
    instance = sample_instance(2, 1)
    assert audit.order_leaks(instance) == []
    # Number the mails again, process after process and case after case, noise first.
    by_truth = sorted(instance.emails, key=lambda mail: (mail.case.process, mail.case.id) if mail.case else ("", ""))
    for position, mail in enumerate(by_truth, start=1):
        mail.id = f"m{position:04d}"
    assert audit.order_leaks(instance) == ["the email IDs follow the processes", "the email IDs follow the cases"]


def test_neighbour_excess_is_small_for_mixed_and_large_for_sorted_labels():
    mixed = ["a", "b", "c", "d"] * 10
    assert audit.neighbour_excess(mixed) < 0
    assert audit.neighbour_excess(sorted(mixed)) > audit.ORDER_LIMIT


def test_masking_hides_names_numbers_and_dates():
    one = Email(JANA, UWE, MONDAY, subject="Rechnung B-12345", body="Hallo Uwe,\n\nRechnung vom 03.03.2025.\n\nJana Wolff")
    other = Email(UWE, JANA, MONDAY, subject="Rechnung B-99", body="Hallo Jana,\n\nRechnung vom 17.04.2025.\n\nUwe Kranz")
    different = Email(JANA, UWE, MONDAY, subject="Rechnung B-12345", body="Hallo Uwe,\n\nMahnung vom 03.03.2025.\n\nJana Wolff")
    assert audit.masked(one) == audit.masked(other)
    assert audit.masked(one) != audit.masked(different)


def test_signature_is_the_same_for_the_same_instance_and_differs_between_levels():
    assert audit.signature(sample_instance(1, 2)) == audit.signature(sample_instance(1, 2))
    assert audit.signature(sample_instance(1, 2)) != audit.signature(sample_instance(2, 2))
