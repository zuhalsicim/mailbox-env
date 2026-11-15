"""Writes one instance as a complete Harbor task directory.

    instruction.md              what the agent is asked to do
    task.toml                   limits, and that the verifier runs in its own container
    environment/                the agent's container: mailbox, glossary, catalogue
    tests/                      the verifier's container: grader and truth
    solution/                   the reference answer and the script that hands it in

The truth exists only under tests/ and solution/, which the agent never sees.
"""

import json
import shutil
from email.utils import format_datetime
from pathlib import Path

from mailgen import catalogue
from mailgen.policies import SHORTCUTS, reference
from mailgen.truth import build_truth

GRADER = Path(__file__).parent / "grade.py"

# PLACEHOLDER. The author writes the final task text.
INSTRUCTION = """\
> PLATZHALTER: Dieser Text steht nur hier, damit die Aufgabe läuft. Die endgültige Aufgabenstellung schreibt die Autorin.

# Vorgänge im Postfach finden

In `/app/mailbox/` liegt das Postfach der {company}: eine Datei je E-Mail. Der Dateiname ohne `.eml` ist die ID der E-Mail.

- `/app/catalogue.json` beschreibt {entries} Vorgangsarten. Nur ein Teil davon kommt im Postfach vor.
- `/app/glossary.json` beschreibt die Schrittarten, aus denen die Vorgänge bestehen.

Finde heraus, welche Vorgangsarten vorkommen, welche E-Mails zu welcher gehören und wie jede abläuft. Schreibe das Ergebnis nach `/app/answer.json`:

```json
{{
  "processes": [
    {{
      "id": "K00",
      "name": "freier Text, wird nicht bewertet",
      "emails": ["m0001", "m0002"],
      "flow": [["ANFRAGE", "ANGEBOT"], ["ANGEBOT", "BESTELLUNG"]]
    }}
  ],
  "noise": ["m0003"]
}}
```

- `processes`: ein Eintrag je Vorgangsart, die im Postfach vorkommt, mit ihrer ID aus dem Katalog.
- `emails`: alle E-Mails dieser Vorgangsart.
- `flow`: Das Paar `[A, B]` gehört dazu, wenn in mindestens einem Fall auf eine E-Mail der Schrittart A zeitlich direkt eine E-Mail der Schrittart B folgt.
- `noise`: alle E-Mails, die zu keinem Vorgang gehören.
"""

TASK_TOML = """\
schema_version = "1.0"
artifacts = ["/app/"]

[task]
name = "mailbox/l{level}-s{seed:04d}"
description = "Find the processes in the mailbox of an invented company."

[metadata]
level = {level}
seed = {seed}

[verifier]
timeout_sec = 120.0
environment_mode = "separate"

[agent]
timeout_sec = 1800.0

[environment]
build_timeout_sec = 600.0
cpus = 1
memory_mb = 1024
storage_mb = 2048
"""

ENVIRONMENT_DOCKERFILE = """\
FROM python:3.13-slim-bookworm
WORKDIR /app
COPY mailbox /app/mailbox
COPY glossary.json catalogue.json /app/
"""

TESTS_DOCKERFILE = """\
FROM python:3.13-slim-bookworm
COPY . /tests/
RUN mkdir -p /app
"""

TEST_SH = """\
#!/bin/sh
python3 /tests/grade.py /app/answer.json /tests/expected.json /logs/verifier
"""

# The reference answer is handed in the way an agent hands in its own: as /app/answer.json.
SOLVE_SH = """\
#!/bin/sh
set -eu
cp /solution/answer.json /app/answer.json
"""


def task_name(instance) -> str:
    return f"mailbox-l{instance.level}-s{instance.seed:04d}"


def build_files(instance) -> dict[str, str]:
    """Every file of the task directory, as path -> text."""
    files = {
        "instruction.md": INSTRUCTION.format(company=catalogue.COMPANY, entries=len(catalogue.CATALOGUE)),
        "task.toml": TASK_TOML.format(level=instance.level, seed=instance.seed),
        "environment/Dockerfile": ENVIRONMENT_DOCKERFILE,
        "environment/glossary.json": as_json(glossary()),
        "environment/catalogue.json": as_json(catalogue_entries()),
        "tests/Dockerfile": TESTS_DOCKERFILE,
        "tests/test.sh": TEST_SH,
        "tests/grade.py": GRADER.read_text(encoding="utf-8"),
        "tests/expected.json": as_json(expected(instance)),
        "solution/solve.sh": SOLVE_SH,
        "solution/answer.json": as_json(reference(instance)),
    }
    for mail in instance.emails:
        files[f"environment/mailbox/{mail.id}.eml"] = mail_file(mail)
    return files


def write_task(instance, out_dir) -> Path:
    """Writes the task directory below out_dir and returns its path. An older copy is replaced."""
    task_dir = Path(out_dir) / task_name(instance)
    if task_dir.exists():
        shutil.rmtree(task_dir)
    for name, text in build_files(instance).items():
        path = task_dir / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")
        if path.suffix == ".sh":
            path.chmod(0o755)
    return task_dir


def expected(instance) -> dict:
    """The content of expected.json: the truth, and what each shortcut would answer, for the grader's fingerprints."""
    shortcuts = {name: shortcut(instance) for name, shortcut in SHORTCUTS.items()}
    return {"level": instance.level, "seed": instance.seed, **build_truth(instance.emails), "shortcuts": shortcuts}


def mail_file(mail) -> str:
    headers = [
        f"From: {mail.sender.name} <{mail.sender.address}>",
        f"To: {mail.recipient.name} <{mail.recipient.address}>",
        f"Date: {format_datetime(mail.sent)}",
        f"Subject: {mail.subject}",
        f"Message-ID: {mail.message_id}",
    ]
    if mail.answers:
        headers.append(f"In-Reply-To: {mail.answers.message_id}")
    return "\n".join(headers) + "\n\n" + mail.body + "\n"


def glossary() -> list[dict]:
    return [
        {"step": step_type.name, "keyword": step_type.keyword, "definition": step_type.definition}
        for step_type in catalogue.STEP_TYPES
    ]


def catalogue_entries() -> list[dict]:
    return [{"id": entry.id, "name": entry.name, "matter": entry.matter} for entry in catalogue.CATALOGUE]


def as_json(data) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
