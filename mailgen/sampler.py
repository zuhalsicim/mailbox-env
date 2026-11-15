"""Samples one mailbox for a level and a seed.

Everything random comes from one generator that is seeded with level, seed and
attempt, so the same level and seed give the same mailbox on any machine. A
sample that breaks a guarantee is thrown away and the next attempt is tried.
"""

import random
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from itertools import combinations

from mailgen import catalogue
from mailgen.grade import grade
from mailgen.model import Case, Email, Instance
from mailgen.policies import SHORTCUTS
from mailgen.render import render
from mailgen.truth import build_truth


@dataclass(frozen=True)
class Dial:
    """The difficulty settings of one level."""

    processes: int                    # how many processes occur
    emails: int                       # about how many mails, noise included
    lookalike_pairs: tuple[int, int]  # fewest and most look-alike pairs that share people and things
    triple: bool                      # two of those pairs meet in one process
    shared_people: bool               # the same people take part in several processes
    new_thread: float                 # chance that a mail starts a new thread instead of answering
    wrong_thread: float               # chance that a new thread is sent as an answer to an old mail of another case
    noise: float                      # share of mails that belong to no process
    foreign_subject: float            # chance that the subject does not name the step
    no_keyword: float                 # chance that the wording avoids the glossary's word
    no_reference: float               # chance that an answer or a forward leaves out the case reference
    days: int                         # the cases start within this many days


# A starting point. The pilot runs decide the numbers.
DIAL = {
    1: Dial(processes=3, emails=40, lookalike_pairs=(0, 0), triple=False, shared_people=False,
            new_thread=0.0, wrong_thread=0.0, noise=0.0, foreign_subject=0.0, no_keyword=0.0, no_reference=0.0, days=30),
    2: Dial(processes=5, emails=150, lookalike_pairs=(2, 2), triple=False, shared_people=True,
            new_thread=0.2, wrong_thread=0.0, noise=0.1, foreign_subject=0.3, no_keyword=0.3, no_reference=0.2, days=60),
    3: Dial(processes=8, emails=400, lookalike_pairs=(3, 4), triple=True, shared_people=True,
            new_thread=0.5, wrong_thread=0.3, noise=0.2, foreign_subject=0.6, no_keyword=0.6, no_reference=0.45, days=90),
}

START = datetime(2025, 3, 3, 8, 0, tzinfo=timezone(timedelta(hours=1)))
MAX_ATTEMPTS = 200   # samples tried for one seed before giving up
MAX_STEPS = 12       # longest case, so that a loop in a process graph ends
FORWARD_SHARE = 0.5  # of the mails that start a new thread inside a case, this share forwards the mail before


def sample_instance(level: int, seed: int) -> Instance:
    """The first sample for this level and seed that keeps every guarantee."""
    rejected = []
    for attempt in range(MAX_ATTEMPTS):
        rng = random.Random(f"mailgen-{level}-{seed}-{attempt}")
        instance = build(level, seed, rng)
        problems = broken_guarantees(instance)
        if not problems:
            instance.rejected = rejected
            return instance
        rejected.append(problems[0])
    raise RuntimeError(f"level {level}, seed {seed}: no sample keeps the guarantees, last problem: {rejected[-1]}")


def build(level: int, seed: int, rng) -> Instance:
    dial = DIAL[level]
    processes, lookalikes = choose_processes(dial, rng)
    pools = cast_pools(processes, dial, rng)
    cases = sample_cases(processes, lookalikes, pools, dial, rng)
    emails = [mail for case in cases for mail in case_mails(case, dial, rng)]
    misfile(emails, dial, rng)
    emails += noise_mails(emails, dial, rng)
    render(emails, rng)
    number(emails, rng)
    return Instance(level, seed, processes, lookalikes, cases, emails)


def choose_processes(dial, rng):
    """Which processes occur, and which look-alike pairs among them share people and things."""
    for _ in range(1000):
        chosen = sorted(rng.sample(catalogue.PROCESSES, dial.processes), key=lambda process: process.id)
        ids = [process.id for process in chosen]
        related = [pair for pair in catalogue.LOOKALIKES if pair[0] in ids and pair[1] in ids]
        wanted = rng.randint(*dial.lookalike_pairs)
        if wanted > len(related) or (wanted == 0 and related):
            continue
        pairs = rng.sample(related, wanted)
        if dial.triple and not share_a_process(pairs):
            continue
        return chosen, pairs
    raise ValueError("the catalogue has no set of processes that fits the dial")


def share_a_process(pairs) -> bool:
    members = [process_id for pair in pairs for process_id in pair]
    return len(set(members)) < len(members)


def cast_pools(processes, dial, rng) -> dict:
    """The people each process may use for each role.

    With shared people every process draws from everybody who can play the role.
    Without, each process gets one person per role whom no other process uses.
    """
    pools, used = {}, []
    for process in processes:
        for role in process.roles():
            people = catalogue.PEOPLE[role]
            unused = [person for person in people if person not in used]
            pool = people if dial.shared_people or not unused else [rng.choice(unused)]
            pools[process.id, role] = pool
            used += pool
    return pools


def sample_cases(processes, lookalikes, pools, dial, rng) -> list[Case]:
    """Two cases for every process, then more for random processes until the mailbox is full."""
    wanted = dial.emails * (1 - dial.noise)
    waiting = processes * 2
    cases, mails = [], 0
    while waiting or mails < wanted:
        process = waiting.pop(0) if waiting else rng.choice(processes)
        twin = free_twin(process, cases, lookalikes, rng)
        case = new_case(f"case-{len(cases) + 1:04d}", process, pools, twin, rng)
        cases.append(case)
        mails += len(case.path)
    return cases


def free_twin(process, cases, lookalikes, rng) -> Case | None:
    """A case of a look-alike process that has no twin yet, if there is one."""
    partners = [b if a == process.id else a for a, b in lookalikes if process.id in (a, b)]
    taken = [case.twin for case in cases if case.twin]
    free = [case for case in cases if case.process in partners and not case.twin and case not in taken]
    return rng.choice(free) if free else None


def new_case(case_id: str, process, pools, twin, rng) -> Case:
    """A case with its path, people and named things. A twin hands over what the two processes have in common."""
    other = catalogue.PROCESS_BY_ID[twin.process] if twin else None
    if other and other.things == process.things:
        thing = twin.thing
    else:
        thing = rng.choice(catalogue.THINGS[process.things])
    if other and other.reference == process.reference:
        reference = twin.reference
    else:
        reference = process.reference.format(number=rng.randint(10000, 99999))
    return Case(
        id=case_id,
        process=process.id,
        path=walk(process, rng),
        people=cast(process, pools, twin, rng),
        thing=thing,
        item=process.item.format(thing=thing),
        reference=reference,
        twin=twin,
    )


def walk(process, rng) -> list[str]:
    """One path through the process graph: from the first step until nothing follows."""
    path = [process.steps[0].type]
    while process.step(path[-1]).then and len(path) < MAX_STEPS:
        path.append(rng.choice(process.step(path[-1]).then))
    return path


def cast(process, pools, twin, rng) -> dict:
    """One person per role, nobody twice. A twin case hands over everybody who can play a role here."""
    people = {}
    for role in process.roles():
        busy = list(people.values())
        able = catalogue.PEOPLE[role]
        handed = [person for person in (twin.people.values() if twin else []) if person in able and person not in busy]
        free = [person for person in pools[process.id, role] if person not in busy]
        anyone = [person for person in able if person not in busy]
        people[role] = handed[0] if handed else rng.choice(free or anyone)
    return people


def case_mails(case, dial, rng) -> list[Email]:
    """The mails of one case in the order of time. Each answers the mail before, forwards it, or starts a new thread."""
    process = catalogue.PROCESS_BY_ID[case.process]
    sent = office_hours(START + timedelta(minutes=rng.randrange(dial.days * 24 * 60)), rng)
    mails = []
    for step_type in case.path:
        step = process.step(step_type)
        mail = Email(
            sender=case.people[step.sender],
            recipient=case.people[step.recipient],
            sent=sent,
            case=case,
            step=step_type,
            names_step=rng.random() >= dial.foreign_subject,
            uses_keyword=rng.random() >= dial.no_keyword,
        )
        if mails and rng.random() >= dial.new_thread:
            mail.answers = mails[-1]
        elif mails and rng.random() < FORWARD_SHARE:
            mail.forwards = mails[-1]
        # Only a mail that hangs on an older mail of its case may leave the reference out:
        # there it can still be looked up. A mail that starts a thread always carries it.
        if mail.answers or mail.forwards:
            mail.shows_reference = rng.random() >= dial.no_reference
        mails.append(mail)
        sent = office_hours(sent + timedelta(minutes=rng.randrange(60, 4 * 24 * 60)), rng)
    return mails


def office_hours(moment: datetime, rng) -> datetime:
    """The same moment if the office is open (weekdays, 8 to 17 o'clock), else some time on the next day it is."""
    if moment.weekday() < 5 and 8 <= moment.hour < 17:
        return moment
    if moment.hour >= 17:
        moment += timedelta(days=1)
    while moment.weekday() > 4:
        moment += timedelta(days=1)
    return moment.replace(hour=rng.randrange(8, 17), minute=rng.randrange(60))


def misfile(emails, dial, rng) -> None:
    """Some mails that start a thread are instead sent as an answer to an old mail of another case
    between the same two people."""
    for mail in emails:
        if mail.answers or mail.forwards or rng.random() >= dial.wrong_thread:
            continue
        older = [
            other for other in emails
            if other.case is not mail.case and other.sent < mail.sent
            and {other.sender, other.recipient} == {mail.sender, mail.recipient}
        ]
        if older:
            mail.answers = rng.choice(older)


def noise_mails(emails, dial, rng) -> list[Email]:
    """Mails that belong to no process, as many as the dial's share of the mailbox."""
    staff = catalogue.PEOPLE["Mitarbeiter"]
    mails = []
    for _ in range(round(len(emails) * dial.noise / (1 - dial.noise))):
        kind = rng.choice(catalogue.NOISE)
        if kind.auto_reply:
            old = rng.choice(emails)
            mail = Email(old.recipient, old.sender, old.sent + timedelta(minutes=1), noise=kind.name, answers=old)
        else:
            sender = kind.sender or rng.choice(staff)
            recipient = rng.choice([person for person in staff if person != sender])
            sent = office_hours(START + timedelta(minutes=rng.randrange(dial.days * 24 * 60)), rng)
            mail = Email(sender, recipient, sent, noise=kind.name)
        mails.append(mail)
    return mails


def number(emails, rng) -> None:
    """Shuffles the mails and gives them neutral IDs, so that neither an ID nor the file order says anything."""
    rng.shuffle(emails)
    for position, mail in enumerate(emails, start=1):
        mail.id = f"m{position:04d}"
        mail.message_id = f"<{rng.getrandbits(64):016x}@{mail.sender.address.split('@')[1]}>"


def broken_guarantees(instance) -> list[str]:
    """What is wrong with an instance. An empty list means it keeps every guarantee."""
    problems = []
    for one, other in combinations(instance.processes, 2):
        if not differ(one, other):
            problems.append(f"{one.id} and {other.id} differ in neither roles, step order nor named things")
    truth = build_truth(instance.emails)
    for name, shortcut in SHORTCUTS.items():
        if grade(shortcut(instance), truth)["reward"] == 1:
            problems.append(f"the shortcut {name} gives the right answer")
    biggest = max(len(process["emails"]) for process in truth["processes"].values())
    if 2 * biggest > len(instance.emails):
        problems.append("one process holds more than half of the emails")
    return problems


def differ(one, other) -> bool:
    """Two processes can be told apart by who writes to whom, by the order of steps or by the things they name."""
    return one.who_to_whom() != other.who_to_whom() or one.order() != other.order() or one.things != other.things
