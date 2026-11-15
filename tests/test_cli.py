"""The three commands of the command line."""

import json
import re
from pathlib import Path

from mailgen.cli import main


def test_generate_writes_a_task_and_grade_scores_its_reference_answer(tmp_path, capsys):
    assert main(["generate", "--level", "1", "--seed", "3", "--out", str(tmp_path)]) == 0
    task_dir = Path(capsys.readouterr().out.strip())
    assert task_dir == tmp_path / "mailbox-l1-s0003"
    assert main(["grade", str(task_dir / "solution" / "answer.json"), str(task_dir / "tests" / "expected.json")]) == 0
    assert json.loads(capsys.readouterr().out)["reward"] == 1


def test_grade_gives_0_for_an_answer_that_is_not_there(tmp_path, capsys):
    main(["generate", "--level", "1", "--seed", "3", "--out", str(tmp_path)])
    capsys.readouterr()
    main(["grade", str(tmp_path / "nothing.json"), str(tmp_path / "mailbox-l1-s0003" / "tests" / "expected.json")])
    assert json.loads(capsys.readouterr().out)["reward"] == 0


def test_audit_prints_the_numbers_and_passes(capsys):
    assert main(["audit", "--n", "3"]) == 0
    printed = capsys.readouterr().out
    assert re.search(r"^instances +3$", printed, re.MULTILINE)
    assert re.search(r"^leak hits +0$", printed, re.MULTILINE)
    assert printed.strip().endswith("audit passed")
