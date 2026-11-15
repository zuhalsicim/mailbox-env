"""Grades an answer against the truth.

This file stands alone: it is copied into the verifier container of every
task, so it uses the standard library only and nothing from this package.

Reward 1 only if every process has exactly the right emails and exactly the
right flow, and the noise is exactly right. Everything else is reward 0 with a
reason. The diagnostics next to the reward are for reading, not a score.
"""

import json
import sys
from pathlib import Path


def grade_file(answer_path, expected_path) -> dict:
    expected = json.loads(Path(expected_path).read_text(encoding="utf-8"))
    try:
        text = Path(answer_path).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return failed("the answer file is missing or cannot be read")
    try:
        answer = json.loads(text)
    except (ValueError, RecursionError):
        return failed("the answer file is not valid JSON")
    return grade(answer, expected)


def grade(answer, expected) -> dict:
    """Compares a parsed answer with the truth. Never raises, whatever the answer looks like."""
    problem = "there is no answer" if answer is None else shape_problem(answer)
    if problem:
        return failed(problem)

    wrong, report = [], {}
    matched, extra = match_processes(answer["processes"], expected["processes"])
    for process_id, truth in expected["processes"].items():
        mine = matched[process_id] or {"emails": [], "flow": []}
        emails = compare(mine["emails"], truth["emails"])
        edges = compare(map(tuple, mine["flow"]), map(tuple, truth["flow"]))
        report[process_id] = {
            "found": matched[process_id] is not None,
            "emails_exact": emails["exact"],
            "emails_precision": emails["precision"],
            "emails_recall": emails["recall"],
            "flow_exact": edges["exact"],
            "edges_hit": edges["hit"],
            "edges_missed": edges["missed"],
            "edges_extra": edges["extra"],
        }
        if not emails["exact"]:
            wrong.append(f"{process_id}: emails differ")
        if not edges["exact"]:
            wrong.append(f"{process_id}: flow differs")
    for process_id in extra:
        wrong.append(f"{process_id}: not a process of this mailbox")
    noise = compare(answer["noise"], expected["noise"])
    if not noise["exact"]:
        wrong.append("noise differs")

    return {
        "reward": 0 if wrong else 1,
        "reason": "; ".join(wrong) or "everything is right",
        "processes": report,
        "extra_processes": extra,
        "noise_exact": noise["exact"],
        "noise_precision": noise["precision"],
        "noise_recall": noise["recall"],
        "fingerprints": fingerprints(answer, expected),
    }


def failed(reason: str) -> dict:
    return {"reward": 0, "reason": reason}


def shape_problem(answer) -> str | None:
    """Says what is wrong with the form of an answer, or None if it can be graded."""
    if not isinstance(answer, dict):
        return "the answer is not a JSON object"
    if not isinstance(answer.get("processes"), list):
        return "'processes' is not a list"
    if not is_string_list(answer.get("noise")):
        return "'noise' is not a list of email IDs"
    for process in answer["processes"]:
        if not isinstance(process, dict):
            return "a process is not a JSON object"
        if not isinstance(process.get("id"), str):
            return "a process has no 'id'"
        if not is_string_list(process.get("emails")):
            return f"{process['id']}: 'emails' is not a list of email IDs"
        flow = process.get("flow")
        if not isinstance(flow, list) or not all(is_string_list(edge) and len(edge) == 2 for edge in flow):
            return f"{process['id']}: 'flow' is not a list of pairs of step types"
    ids = [process["id"] for process in answer["processes"]]
    if len(set(ids)) != len(ids):
        return "a process ID is given twice"
    return None


def is_string_list(value) -> bool:
    return isinstance(value, list) and all(isinstance(item, str) for item in value)


def match_processes(given: list, expected: dict) -> tuple[dict, list]:
    """Decides which process of the answer is compared with which true process.

    Here they are matched by catalogue ID. Returns the answer's process for every
    true process (None if it is missing) and the IDs the answer gives too many.
    This is the only place that knows how they are matched, so a mode without a
    catalogue can match by largest overlap here.
    """
    by_id = {process["id"]: process for process in given}
    matched = {process_id: by_id.get(process_id) for process_id in expected}
    extra = sorted(process_id for process_id in by_id if process_id not in expected)
    return matched, extra


def compare(given, wanted) -> dict:
    given, wanted = set(given), set(wanted)
    hit = given & wanted
    return {
        "exact": given == wanted,
        "precision": round(len(hit) / len(given), 3) if given else 1.0,
        "recall": round(len(hit) / len(wanted), 3) if wanted else 1.0,
        "hit": sorted(hit),
        "missed": sorted(wanted - given),
        "extra": sorted(given - wanted),
    }


def fingerprints(answer, expected) -> dict:
    """Names of the known shortcuts whose mistake the answer repeats exactly.

    "emails" lists the shortcuts that sort the emails wrongly and in the very same
    way as the answer, "flow" those that get the flows wrong in the very same way.
    """
    truth = {
        "processes": [{"id": process_id, **process} for process_id, process in expected["processes"].items()],
        "noise": expected["noise"],
    }
    same = {"emails": [], "flow": []}
    for name, shortcut in expected.get("shortcuts", {}).items():
        if not shortcut:
            continue
        if grouping(shortcut) == grouping(answer) and grouping(shortcut) != grouping(truth):
            same["emails"].append(name)
        if flows(shortcut) == flows(answer) and flows(shortcut) != flows(truth):
            same["flow"].append(name)
    return same


def grouping(answer) -> dict:
    groups = {process["id"]: set(process["emails"]) for process in answer["processes"]}
    groups["noise"] = set(answer["noise"])
    return groups


def flows(answer) -> dict:
    return {process["id"]: set(map(tuple, process["flow"])) for process in answer["processes"]}


def main(argv) -> int:
    """grade.py ANSWER EXPECTED [OUT_DIR]: prints the result; with OUT_DIR also writes reward.txt and diagnostics.json."""
    answer_path, expected_path = argv[0], argv[1]
    out_dir = Path(argv[2]) if len(argv) > 2 else None
    if out_dir:
        out_dir.mkdir(parents=True, exist_ok=True)
        # The reward is 0 until the grading has finished, so a crash can never count as a pass.
        (out_dir / "reward.txt").write_text("0")
    result = grade_file(answer_path, expected_path)
    report = json.dumps(result, indent=2, sort_keys=True)
    print(report)
    if out_dir:
        (out_dir / "diagnostics.json").write_text(report + "\n", encoding="utf-8")
        (out_dir / "reward.txt").write_text(str(result["reward"]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
