"""The data the generator works with: process definitions, cases, emails, instances."""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class Person:
    name: str
    address: str

    @property
    def first_name(self) -> str:
        return self.name.split()[0]


@dataclass(frozen=True)
class StepType:
    """One entry of the glossary."""

    name: str        # the closed value an answer uses, e.g. "ANGEBOT"
    keyword: str     # the glossary's word for it, e.g. "Angebot"
    definition: str  # one sentence


@dataclass(frozen=True)
class Step:
    """One node of a process graph: who writes which kind of mail to whom, and what may follow."""

    type: str
    sender: str                 # a role
    recipient: str              # a role
    then: tuple[str, ...] = ()  # step types that may come next; several are a branch, none ends the case


@dataclass(frozen=True)
class CatalogueEntry:
    """A case type as the agent sees it: an ID, a name and one sentence on the business matter."""

    id: str
    name: str
    matter: str


@dataclass(frozen=True)
class Process:
    """A catalogue entry that can occur in a mailbox, with its graph.

    The first step starts every case. A step is optional when a branch leads around it.
    """

    id: str
    name: str
    matter: str
    steps: tuple[Step, ...]
    things: str     # name of the list of things its cases are about
    item: str       # how a mail names the thing, with the slot {thing}
    reference: str  # pattern of the case reference, with the slot {number}

    def step(self, step_type: str) -> Step:
        return next(step for step in self.steps if step.type == step_type)

    def roles(self) -> list[str]:
        """All roles, in the order in which they first appear."""
        roles = []
        for step in self.steps:
            for role in (step.sender, step.recipient):
                if role not in roles:
                    roles.append(role)
        return roles

    def who_to_whom(self) -> set[tuple[str, str]]:
        return {(step.sender, step.recipient) for step in self.steps}

    def order(self) -> set[tuple[str, str]]:
        return {(step.type, later) for step in self.steps for later in step.then}


@dataclass(frozen=True)
class NoiseKind:
    """A kind of mail that belongs to no process."""

    name: str
    sender: Person | None = None  # None: somebody from the staff
    auto_reply: bool = False      # sent as an answer to a mail of a process


@dataclass(eq=False)
class Case:
    """One run of a process: its path through the graph, its people and the things it names."""

    id: str
    process: str  # catalogue ID
    path: list[str] = field(default_factory=list)            # step types in order
    people: dict[str, Person] = field(default_factory=dict)  # role -> person
    thing: str = ""
    item: str = ""
    reference: str = ""
    twin: "Case | None" = None  # the case of a look-alike process it shares people and things with


@dataclass(eq=False)
class Email:
    """One mail. The sampler decides what it is, the renderer writes it, the numbering names it."""

    sender: Person
    recipient: Person
    sent: datetime
    case: Case | None = None         # None: noise
    step: str | None = None          # step type; None: noise
    noise: str | None = None         # kind of noise; None: part of a case
    answers: "Email | None" = None   # the mail this one replies to
    forwards: "Email | None" = None  # the mail this one forwards, which starts a new thread
    names_step: bool = True          # the subject names the step
    uses_keyword: bool = True        # the wording uses the glossary's word
    shows_reference: bool = True     # the mail carries the case reference
    subject: str = ""
    text: str = ""                   # what the sender wrote, without the quoted mail
    body: str = ""                   # text plus the quoted mail
    id: str = ""                     # neutral, given after shuffling
    message_id: str = ""


@dataclass
class Instance:
    """One generated mailbox with everything that is known about it."""

    level: int
    seed: int
    processes: list[Process]           # the processes that occur
    lookalikes: list[tuple[str, str]]  # the look-alike pairs that share people and things
    cases: list[Case]
    emails: list[Email]                # in the order of their IDs
    rejected: list[str] = field(default_factory=list)  # why earlier samples for this seed were thrown away
