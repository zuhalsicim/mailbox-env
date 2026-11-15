"""Writes subject and body of every mail from the templates.

The templates are a data file. The sampler has already decided what each mail
is; here only the wording is chosen and the slots are filled.
"""

import functools
import tomllib
from pathlib import Path

TEMPLATES = Path(__file__).parent / "templates" / "placeholder.toml"


@functools.cache
def load_templates(path: Path = TEMPLATES) -> dict:
    with open(path, "rb") as file:
        return tomllib.load(file)


def render(emails, rng, templates=None):
    """Fills in subject, text and body. Older mails first, because an answer quotes the mail before it."""
    templates = templates or load_templates()
    for mail in sorted(emails, key=lambda mail: mail.sent):
        slots = slots_of(mail)
        mail.subject = subject_of(mail, templates, slots, rng)
        mail.text = text_of(mail, templates, slots, rng)
        mail.body = mail.text + quote_of(mail, templates, slots)


def slots_of(mail) -> dict:
    old = mail.answers or mail.forwards
    return {
        "sender": mail.sender.name,
        "recipient": mail.recipient.name,
        "sender_first": mail.sender.first_name,
        "recipient_first": mail.recipient.first_name,
        "item": mail.case.item if mail.case else "",
        "ref": mail.case.reference if mail.case else "",
        "subject": old.subject if old else "",
        "date": old.sent.strftime("%d.%m.%Y %H:%M") if old else "",
    }


def subject_of(mail, templates, slots, rng) -> str:
    layout = templates["layout"]
    if mail.noise:
        return rng.choice(templates["noise"][mail.noise]["subjects"]).format(**slots)
    if mail.forwards:
        return layout["forward_subject"].format(**slots)
    if not mail.names_step:
        # The subject says nothing about this step: it repeats the old one or is a stock phrase.
        if mail.answers:
            return layout["reply_subject"].format(**slots)
        return rng.choice(layout["generic_subjects"]).format(**slots)
    own = templates["step"][mail.step]["subject"]
    if mail.shows_reference:
        return layout["subject_with_reference"].format(**{**slots, "subject": own})
    return own


def text_of(mail, templates, slots, rng) -> str:
    layout = templates["layout"]
    if mail.noise:
        return rng.choice(templates["noise"][mail.noise]["texts"]).format(**slots)
    wordings = templates["step"][mail.step]["with_keyword" if mail.uses_keyword else "without_keyword"]
    lines = [rng.choice(layout["greetings"]), "", rng.choice(wordings)]
    if mail.shows_reference:
        lines.append(layout["reference_line"])
    lines += ["", rng.choice(layout["closings"])]
    return "\n".join(lines).format(**slots)


def quote_of(mail, templates, slots) -> str:
    """The answered or forwarded mail, repeated below the new text as mail programs do."""
    layout = templates["layout"]
    old = mail.answers or mail.forwards
    if not old:
        return ""
    # In the line above the quote, the sender is the one who wrote the old mail.
    writer = {"sender": old.sender.name, "sender_first": old.sender.first_name}
    header = layout["forward_header" if mail.forwards else "quote_header"].format(**{**slots, **writer})
    lines = old.text.splitlines()
    if mail.answers:
        lines = ["> " + line for line in lines]
    return "\n\n" + header + "\n" + "\n".join(lines)
