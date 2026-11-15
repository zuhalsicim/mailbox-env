"""Checks a batch of generated instances.

Reported as numbers: samples the guarantees threw away, mails that are equal
once names, numbers and dates are masked, and instances whose processes have
the same shape. The audit fails if an agent-visible file gives the truth away,
if the reference answer does not earn reward 1, or if a shortcut does not earn
reward 0.
"""

import hashlib
import json
import math
import re
from collections import Counter

from mailgen import catalogue
from mailgen.grade import grade
from mailgen.package import build_files, expected
from mailgen.policies import SHORTCUTS, reference
from mailgen.sampler import broken_guarantees, sample_instance
from mailgen.truth import build_truth

LEVELS = (1, 2, 3)
MAIL_PATH = re.compile(r"environment/mailbox/m\d{4}\.eml")
OTHER_AGENT_FILES = ("instruction.md", "environment/Dockerfile", "environment/glossary.json", "environment/catalogue.json")
HEADERS = ("From", "To", "Date", "Subject", "Message-ID", "In-Reply-To")
# Neighbouring IDs may share a label this many standard deviations more often than chance before it counts as a leak.
ORDER_LIMIT = 6.0


def run(n: int, files_of=build_files) -> dict:
    """Audits n instances, spread evenly over the levels, seeds counting from 1.

    files_of turns an instance into its task files; a test passes its own to plant a leak.
    """
    report = {
        "instances": 0, "emails": 0, "rejected": Counter(), "leaks": [], "failures": [],
        "reference_1": 0, "shortcut_0": Counter(),
    }
    masked_mails, signatures = set(), {level: set() for level in LEVELS}
    for level in LEVELS:
        for seed in range(1, n // len(LEVELS) + 1):
            instance = sample_instance(level, seed)
            name = f"level {level}, seed {seed}"
            report["instances"] += 1
            report["emails"] += len(instance.emails)
            report["rejected"].update(instance.rejected)
            report["leaks"] += [f"{name}: {hit}" for hit in leaks(instance, files_of(instance))]
            report["failures"] += [f"{name}: {problem}" for problem in broken_guarantees(instance)]
            masked_mails.update(masked(mail) for mail in instance.emails)
            signatures[level].add(signature(instance))
            truth = expected(instance)
            if grade(reference(instance), truth)["reward"] == 1:
                report["reference_1"] += 1
            else:
                report["failures"].append(f"{name}: the reference answer does not earn reward 1")
            for shortcut in SHORTCUTS:
                if grade(truth["shortcuts"][shortcut], truth)["reward"] == 0:
                    report["shortcut_0"][shortcut] += 1
                else:
                    report["failures"].append(f"{name}: the shortcut {shortcut} does not earn reward 0")
    report["duplicate_emails"] = report["emails"] - len(masked_mails)
    report["signatures"] = {level: len(found) for level, found in signatures.items()}
    report["duplicate_instances"] = report["instances"] - sum(report["signatures"].values())
    report["passed"] = not report["leaks"] and not report["failures"]
    return report


def summary(report: dict) -> str:
    by_level = ", ".join(f"level {level}: {count}" for level, count in report["signatures"].items())
    lines = [
        f"instances            {report['instances']}",
        f"emails               {report['emails']}",
        f"rejected samples     {sum(report['rejected'].values())}",
        *[f"    {count:5d}  {reason}" for reason, count in sorted(report["rejected"].items())],
        f"duplicate emails     {report['duplicate_emails']} (equal after masking names, numbers and dates)",
        f"signatures           {sum(report['signatures'].values())} ({by_level})",
        f"duplicate instances  {report['duplicate_instances']} (same signature as an earlier instance)",
        f"leak hits            {len(report['leaks'])}",
        f"reference reward 1   {report['reference_1']} of {report['instances']}",
        *[f"{name + ' reward 0':<27}{report['shortcut_0'][name]} of {report['instances']}" for name in SHORTCUTS],
        *report["leaks"],
        *report["failures"],
        "audit passed" if report["passed"] else "audit FAILED",
    ]
    return "\n".join(lines)


def masked(mail) -> str:
    """Subject and body with names and numbers blanked. Dates are written in digits, so they go with the numbers."""
    text = mail.subject + "\n" + mail.body
    for name in NAMES:
        text = text.replace(name, "NAME")
    return re.sub(r"\d+", "0", text)


def _names() -> list[str]:
    people = [person for group in catalogue.PEOPLE.values() for person in group]
    people += [kind.sender for kind in catalogue.NOISE if kind.sender]
    names = {name for person in people for name in (person.name, person.first_name)}
    return sorted(names, key=lambda name: (-len(name), name))  # full names before first names


NAMES = _names()


def signature(instance) -> str:
    """What makes two instances the same task: for every process, the shape of its flow and who writes to whom."""
    truth = build_truth(instance.emails)
    shape = [
        [truth["processes"][process.id]["flow"], sorted(process.who_to_whom())]
        for process in instance.processes
    ]
    return hashlib.sha256(json.dumps(shape).encode("utf-8")).hexdigest()[:16]


def leaks(instance, files: dict[str, str]) -> list[str]:
    """Everything in the agent's files that gives the truth away. An empty list means the instance is clean."""
    case_ids = [case.id for case in instance.cases]
    labels = [entry.id for entry in catalogue.CATALOGUE] + [step_type.name for step_type in catalogue.STEP_TYPES]
    in_any_file = word_pattern(case_ids)
    in_a_mail = word_pattern(case_ids + labels)
    hits = []
    for path, text in sorted(files.items()):
        if path != "instruction.md" and not path.startswith("environment/"):
            continue  # the agent never sees tests/, solution/ and task.toml
        is_mail = MAIL_PATH.fullmatch(path) is not None
        if not is_mail and path not in OTHER_AGENT_FILES:
            hits.append(f"{path}: a file the agent should not have")
        for word in sorted(set((in_a_mail if is_mail else in_any_file).findall(path + "\n" + text))):
            hits.append(f"{path}: contains {word}")
        if is_mail:
            for line in text.split("\n\n")[0].splitlines():
                if line.split(":")[0] not in HEADERS:
                    hits.append(f"{path}: unexpected header {line.split(':')[0]}")
    return hits + order_leaks(instance)


def word_pattern(words):
    return re.compile(r"\b(?:" + "|".join(re.escape(word) for word in words) + r")\b")


def order_leaks(instance) -> list[str]:
    """IDs and file order must say nothing: neighbours share case or process no more often than chance explains."""
    mails = sorted(instance.emails, key=lambda mail: mail.id)
    by_process = [mail.case.process if mail.case else None for mail in mails]
    by_case = [mail.case.id if mail.case else None for mail in mails]
    hits = []
    if neighbour_excess(by_process) > ORDER_LIMIT:
        hits.append("the email IDs follow the processes")
    if neighbour_excess(by_case) > ORDER_LIMIT:
        hits.append("the email IDs follow the cases")
    return hits


def neighbour_excess(labels) -> float:
    """How many standard deviations more often than chance two neighbours carry the same label."""
    pairs = len(labels) - 1
    chance = sum(size * (size - 1) for size in Counter(labels).values()) / (len(labels) * pairs)
    same = sum(one == other for one, other in zip(labels, labels[1:]))
    spread = math.sqrt(pairs * chance * (1 - chance))
    return (same - pairs * chance) / spread if spread else 0.0
