"""The task directory has the layout Harbor expects and keeps the truth away from the agent."""

import json
import os
import tomllib
from pathlib import Path

from mailgen import catalogue
from mailgen import grade as grader
from mailgen.package import build_files, task_name, write_task
from mailgen.sampler import sample_instance


def test_layout(instance):
    files = build_files(instance)
    fixed = {
        "instruction.md", "task.toml",
        "environment/Dockerfile", "environment/glossary.json", "environment/catalogue.json",
        "tests/Dockerfile", "tests/test.sh", "tests/grade.py", "tests/expected.json",
        "solution/solve.sh", "solution/answer.json",
    }
    mails = {f"environment/mailbox/{mail.id}.eml" for mail in instance.emails}
    assert set(files) == fixed | mails
    assert len(mails) == len(instance.emails)


def test_task_toml_asks_for_a_separate_verifier(instance):
    config = tomllib.loads(build_files(instance)["task.toml"])
    assert config["verifier"]["environment_mode"] == "separate"
    assert config["artifacts"] == ["/app/"]
    assert config["task"]["name"] == f"mailbox/l{instance.level}-s{instance.seed:04d}"


def test_grader_in_the_task_is_the_grader_of_the_package(instance):
    assert build_files(instance)["tests/grade.py"] == Path(grader.__file__).read_text(encoding="utf-8")


def test_reference_answer_earns_1_against_the_packaged_truth(instance):
    files = build_files(instance)
    result = grader.grade(json.loads(files["solution/answer.json"]), json.loads(files["tests/expected.json"]))
    assert result["reward"] == 1
    assert result["fingerprints"] == {"emails": [], "flow": []}


def test_agent_gets_the_whole_catalogue_and_glossary(instance):
    files = build_files(instance)
    assert len(json.loads(files["environment/catalogue.json"])) == len(catalogue.CATALOGUE)
    assert len(json.loads(files["environment/glossary.json"])) == len(catalogue.STEP_TYPES)


def test_a_mail_file_has_headers_a_blank_line_and_the_body(instance):
    files = build_files(instance)
    by_message_id = {mail.message_id: mail for mail in instance.emails}
    for mail in instance.emails:
        head, body = files[f"environment/mailbox/{mail.id}.eml"].split("\n\n", 1)
        headers = dict(line.split(": ", 1) for line in head.splitlines())
        assert headers["Subject"] == mail.subject
        assert headers["From"] == f"{mail.sender.name} <{mail.sender.address}>"
        assert body == mail.body + "\n"
        assert ("In-Reply-To" in headers) == (mail.answers is not None)
        if mail.answers:
            assert by_message_id[headers["In-Reply-To"]] is mail.answers


def test_write_task_writes_every_file(tmp_path):
    instance = sample_instance(1, 3)
    task_dir = write_task(instance, tmp_path)
    assert task_dir == tmp_path / task_name(instance)
    written = {path.relative_to(task_dir).as_posix() for path in task_dir.rglob("*") if path.is_file()}
    assert written == set(build_files(instance))
    if os.name == "posix":
        assert os.access(task_dir / "tests" / "test.sh", os.X_OK)
        assert os.access(task_dir / "solution" / "solve.sh", os.X_OK)


def test_write_task_replaces_an_older_copy(tmp_path):
    instance = sample_instance(1, 3)
    task_dir = write_task(instance, tmp_path)
    (task_dir / "environment" / "mailbox" / "left-over.eml").write_text("old")
    write_task(instance, tmp_path)
    assert not (task_dir / "environment" / "mailbox" / "left-over.eml").exists()
