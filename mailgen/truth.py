"""What is true about a mailbox: which mail belongs to which case and process, and how each process flows."""


def directly_follows(traces) -> list[list[str]]:
    """The directly-follows graph of some traces.

    A trace is the list of step types of one case in the order of time. The
    pair (A, B) is in the graph if B comes directly after A in at least one trace.
    """
    edges = {(a, b) for trace in traces for a, b in zip(trace, trace[1:])}
    return [list(edge) for edge in sorted(edges)]


def build_truth(emails) -> dict:
    """Email to case to process, the emails and the flow of every process, and the noise."""
    labels, members, cases = {}, {}, {}
    for mail in sorted(emails, key=lambda mail: (mail.sent, mail.id)):
        case = mail.case
        labels[mail.id] = {
            "case": case.id if case else None,
            "process": case.process if case else None,
            "step": mail.step if case else None,
        }
        if case:
            members.setdefault(case.process, []).append(mail.id)
            cases.setdefault(case.process, {}).setdefault(case.id, []).append(mail)
    processes = {}
    for process in sorted(members):
        traces = [trace_of(mails) for mails in cases[process].values()]
        processes[process] = {"emails": sorted(members[process]), "flow": directly_follows(traces)}
    noise = sorted(mail_id for mail_id, label in labels.items() if label["case"] is None)
    return {"processes": processes, "noise": noise, "emails": dict(sorted(labels.items()))}


def trace_of(mails) -> list[str]:
    """The step types of one case in the order of time. Two mails at the same moment would have no order."""
    for earlier, later in zip(mails, mails[1:]):
        if earlier.sent == later.sent:
            raise ValueError(f"case {earlier.case.id} has two mails at {earlier.sent}")
    return [mail.step for mail in mails]
