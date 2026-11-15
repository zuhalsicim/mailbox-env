"""The grader on answers made by hand."""

import copy
import json

import pytest

from mailgen import grade as grader
from mailgen.grade import grade, grade_file

EXPECTED = {
    "processes": {
        "K01": {"emails": ["m1", "m2", "m3"], "flow": [["A", "B"], ["B", "C"]]},
        "K07": {"emails": ["m4", "m5"], "flow": [["A", "C"]]},
    },
    "noise": ["m6"],
}


def right_answer():
    return {
        "processes": [
            {"id": "K07", "name": "second", "emails": ["m5", "m4"], "flow": [["A", "C"]]},
            {"id": "K01", "name": "first", "emails": ["m3", "m1", "m2"], "flow": [["B", "C"], ["A", "B"]]},
        ],
        "noise": ["m6"],
    }


def process(answer, process_id):
    return next(entry for entry in answer["processes"] if entry["id"] == process_id)


def test_exact_answer_earns_1_whatever_the_order_and_the_names():
    result = grade(right_answer(), EXPECTED)
    assert result["reward"] == 1
    assert result["processes"]["K01"]["emails_exact"] and result["processes"]["K01"]["flow_exact"]


def test_one_email_in_the_wrong_place_earns_0():
    answer = right_answer()
    process(answer, "K01")["emails"].remove("m3")
    answer["noise"].append("m3")
    result = grade(answer, EXPECTED)
    assert result["reward"] == 0
    assert result["processes"]["K01"]["emails_precision"] == 1.0
    assert result["processes"]["K01"]["emails_recall"] == pytest.approx(0.667)
    assert result["noise_precision"] == 0.5
    assert "K01: emails differ" in result["reason"] and "noise differs" in result["reason"]


def test_one_missing_edge_earns_0():
    answer = right_answer()
    process(answer, "K01")["flow"].remove(["B", "C"])
    result = grade(answer, EXPECTED)
    assert result["reward"] == 0
    assert result["processes"]["K01"]["edges_missed"] == [("B", "C")]
    assert result["processes"]["K01"]["emails_exact"]
    assert result["reason"] == "K01: flow differs"


def test_one_edge_too_many_earns_0():
    answer = right_answer()
    process(answer, "K07")["flow"].append(["C", "A"])
    result = grade(answer, EXPECTED)
    assert result["reward"] == 0
    assert result["processes"]["K07"]["edges_extra"] == [("C", "A")]


def test_a_reversed_edge_is_a_wrong_edge():
    answer = right_answer()
    process(answer, "K07")["flow"] = [["C", "A"]]
    assert grade(answer, EXPECTED)["reward"] == 0


def test_a_missing_process_earns_0():
    answer = right_answer()
    answer["processes"] = [process(answer, "K01")]
    result = grade(answer, EXPECTED)
    assert result["reward"] == 0
    assert result["processes"]["K07"]["found"] is False


def test_a_process_that_does_not_occur_earns_0():
    answer = right_answer()
    answer["processes"].append({"id": "K02", "emails": [], "flow": []})
    result = grade(answer, EXPECTED)
    assert result["reward"] == 0
    assert result["extra_processes"] == ["K02"]


def test_right_emails_under_the_wrong_id_earn_0():
    answer = right_answer()
    process(answer, "K07")["id"] = "K09"
    assert grade(answer, EXPECTED)["reward"] == 0


@pytest.mark.parametrize("answer", [
    None,
    {},
    [],
    "text",
    42,
    {"processes": [], "noise": []},
    {"processes": "K01", "noise": []},
    {"processes": [], "noise": "m6"},
    {"processes": [], "noise": [6]},
    {"processes": ["K01"], "noise": []},
    {"processes": [{"emails": [], "flow": []}], "noise": []},
    {"processes": [{"id": 1, "emails": [], "flow": []}], "noise": []},
    {"processes": [{"id": "K01", "emails": "m1", "flow": []}], "noise": []},
    {"processes": [{"id": "K01", "emails": [["m1"]], "flow": []}], "noise": []},
    {"processes": [{"id": "K01", "emails": [], "flow": [["A"]]}], "noise": []},
    {"processes": [{"id": "K01", "emails": [], "flow": [["A", "B", "C"]]}], "noise": []},
    {"processes": [{"id": "K01", "emails": [], "flow": ["AB"]}], "noise": []},
    {"processes": [{"id": "K01", "emails": [], "flow": [[1, 2]]}], "noise": []},
    {"processes": [{"id": "K01", "emails": [], "flow": {}}], "noise": []},
])
def test_empty_and_malformed_answers_earn_0_without_a_crash(answer):
    result = grade(answer, EXPECTED)
    assert result["reward"] == 0
    assert result["reason"]


def test_the_same_process_twice_earns_0():
    answer = right_answer()
    answer["processes"].append(copy.deepcopy(process(answer, "K01")))
    result = grade(answer, EXPECTED)
    assert result["reward"] == 0
    assert "twice" in result["reason"]


def write_expected(tmp_path):
    path = tmp_path / "expected.json"
    path.write_text(json.dumps(EXPECTED), encoding="utf-8")
    return path


@pytest.mark.parametrize("content", [b"", b"{", b"not json", b"\xff\xfe\x00", b"[" * 100000])
def test_files_that_are_not_json_earn_0(tmp_path, content):
    answer_path = tmp_path / "answer.json"
    answer_path.write_bytes(content)
    result = grade_file(answer_path, write_expected(tmp_path))
    assert result["reward"] == 0
    assert result["reason"]


def test_a_missing_file_earns_0(tmp_path):
    result = grade_file(tmp_path / "answer.json", write_expected(tmp_path))
    assert result == {"reward": 0, "reason": "the answer file is missing or cannot be read"}


def expected_with_shortcuts():
    """The truth plus three shortcut answers: one groups wrongly, one has wrong flows, one is right by luck."""
    one_process = {
        "processes": [{"id": "K01", "emails": ["m1", "m2", "m3", "m4", "m5"], "flow": [["A", "B"]]}],
        "noise": ["m6"],
    }
    wrong_steps = right_answer()
    process(wrong_steps, "K01")["flow"] = [["A", "A"]]
    shortcuts = {"all_in_one": one_process, "by_keyword": wrong_steps, "lucky": right_answer(), "no_op": None}
    return {**EXPECTED, "shortcuts": shortcuts}


def test_fingerprint_names_the_shortcut_whose_grouping_the_answer_repeats():
    answer = {
        "processes": [{"id": "K01", "emails": ["m5", "m4", "m3", "m2", "m1"], "flow": [["B", "C"]]}],
        "noise": ["m6"],
    }
    assert grade(answer, expected_with_shortcuts())["fingerprints"] == {"emails": ["all_in_one"], "flow": []}


def test_fingerprint_names_the_shortcut_whose_flow_the_answer_repeats():
    answer = right_answer()
    process(answer, "K01")["flow"] = [["A", "A"]]
    process(answer, "K07")["emails"] = ["m4"]
    assert grade(answer, expected_with_shortcuts())["fingerprints"] == {"emails": [], "flow": ["by_keyword"]}


def test_a_right_answer_has_no_fingerprint_even_if_a_shortcut_is_right_too():
    assert grade(right_answer(), expected_with_shortcuts())["fingerprints"] == {"emails": [], "flow": []}


def test_main_writes_reward_and_diagnostics(tmp_path, capsys):
    answer_path = tmp_path / "answer.json"
    answer_path.write_text(json.dumps(right_answer()), encoding="utf-8")
    out_dir = tmp_path / "logs"
    assert grader.main([str(answer_path), str(write_expected(tmp_path)), str(out_dir)]) == 0
    assert (out_dir / "reward.txt").read_text() == "1"
    assert json.loads((out_dir / "diagnostics.json").read_text(encoding="utf-8"))["reward"] == 1
    assert json.loads(capsys.readouterr().out)["reward"] == 1


def test_main_writes_reward_0_when_there_is_no_answer(tmp_path):
    out_dir = tmp_path / "logs"
    grader.main([str(tmp_path / "answer.json"), str(write_expected(tmp_path)), str(out_dir)])
    assert (out_dir / "reward.txt").read_text() == "0"
