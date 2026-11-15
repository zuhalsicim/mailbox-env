"""Answers that need no understanding of the mail.

The reference answer is built from the truth and must earn reward 1. Every
shortcut must earn reward 0 on every instance; the sampler throws away an
instance on which one of them works.

A shortcut puts mails into groups by one cheap rule and treats every group as
one case. It cannot know which catalogue entry a group is, so it is told: each
group gets the process most of its mails really belong to. That is the best
labelling the shortcut could hope for, so when it fails, it fails because of
its grouping or its step lookup, not because of a wrong name.
"""

from collections import Counter

from mailgen import catalogue
from mailgen.truth import build_truth, directly_follows

NEIGHBOURS = 10  # how many emails with neighbouring IDs form one group


def reference(instance) -> dict:
    truth = build_truth(instance.emails)
    processes = [
        {"id": process_id, "name": catalogue.PROCESS_BY_ID[process_id].name, **truth["processes"][process_id]}
        for process_id in truth["processes"]
    ]
    return {"processes": processes, "noise": truth["noise"]}


def no_op(instance) -> None:
    """Hands in nothing."""
    return None


def all_noise(instance) -> dict:
    return {"processes": [], "noise": sorted(mail.id for mail in instance.emails)}


def all_in_one(instance) -> dict:
    """Every mail goes into the biggest process, and the whole mailbox is read as one case."""
    truth = build_truth(instance.emails)
    biggest = max(truth["processes"], key=lambda process_id: len(truth["processes"][process_id]["emails"]))
    mails = sorted(instance.emails, key=lambda mail: (mail.sent, mail.id))
    steps = [step for step in map(keyword_step, mails) if step]
    process = {"id": biggest, "emails": sorted(mail.id for mail in mails), "flow": directly_follows([steps])}
    return {"processes": [process], "noise": []}


def by_subject(instance) -> dict:
    return answer_from_groups(instance, grouped(instance.emails, lambda mail: bare_subject(mail.subject)))


def by_sender_pair(instance) -> dict:
    return answer_from_groups(instance, grouped(instance.emails, sender_pair))


def by_thread(instance) -> dict:
    return answer_from_groups(instance, grouped(instance.emails, thread_start))


def neighbouring_ids(instance) -> dict:
    return answer_from_groups(instance, grouped(instance.emails, lambda mail: (int(mail.id[1:]) - 1) // NEIGHBOURS))


def by_keyword(instance) -> dict:
    """Knows the true cases; only the step type is looked up by keyword."""
    return answer_from_groups(instance, grouped(instance.emails, lambda mail: mail.case.id if mail.case else mail.id))


SHORTCUTS = {
    "no_op": no_op,
    "all_noise": all_noise,
    "all_in_one": all_in_one,
    "by_subject": by_subject,
    "by_sender_pair": by_sender_pair,
    "by_thread": by_thread,
    "by_keyword": by_keyword,
    "neighbouring_ids": neighbouring_ids,
}


def answer_from_groups(instance, groups) -> dict:
    """Turns groups of mails into an answer: one case per group, steps by keyword, best possible label."""
    truth = build_truth(instance.emails)
    members, traces, noise = {}, {}, []
    for group in groups:
        group = sorted(group, key=lambda mail: (mail.sent, mail.id))
        label = likeliest_process(group, truth)
        if label is None:
            noise += [mail.id for mail in group]
            continue
        steps = [keyword_step(mail) for mail in group]
        members.setdefault(label, []).extend(mail.id for mail in group)
        traces.setdefault(label, []).append([step for step in steps if step])
    processes = [
        {"id": label, "emails": sorted(members[label]), "flow": directly_follows(traces[label])}
        for label in sorted(members)
    ]
    return {"processes": processes, "noise": sorted(noise)}


def grouped(emails, key) -> list[list]:
    groups = {}
    for mail in emails:
        groups.setdefault(key(mail), []).append(mail)
    return list(groups.values())


def likeliest_process(group, truth) -> str | None:
    """The process most mails of the group really belong to; None if most of them are noise."""
    counts = Counter(truth["emails"][mail.id]["process"] for mail in group)
    return counts.most_common(1)[0][0]


def keyword_step(mail) -> str | None:
    """The first step type of the glossary whose word occurs anywhere in the mail, quoted text included."""
    text = (mail.subject + "\n" + mail.body).lower()
    for step_type in catalogue.STEP_TYPES:
        if step_type.keyword.lower() in text:
            return step_type.name
    return None


def bare_subject(subject: str) -> str:
    """The subject without the marks for answers and forwards."""
    text = subject.strip().lower()
    while text.startswith(("aw:", "wg:", "re:", "fw:")):
        text = text[3:].strip()
    return text


def sender_pair(mail) -> tuple[str, str]:
    """The two people of a mail, whoever of them wrote it."""
    first, second = sorted([mail.sender.address, mail.recipient.address])
    return first, second


def thread_start(mail) -> str:
    """The ID of the first mail of the thread, found by following the answers back."""
    while mail.answers:
        mail = mail.answers
    return mail.id
