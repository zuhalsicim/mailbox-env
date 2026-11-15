"""The sample catalogue and the placeholder templates fit together.

These tests are for whoever edits catalogue.py or the templates file: they say
at once when a step has no template or a wording breaks its own rule.
"""

from itertools import combinations

from mailgen import catalogue
from mailgen.render import load_templates
from mailgen.sampler import differ

KEYWORD = {step_type.name: step_type.keyword for step_type in catalogue.STEP_TYPES}


def test_catalogue_has_twelve_entries_and_eight_of_them_can_occur():
    ids = [entry.id for entry in catalogue.CATALOGUE]
    assert len(ids) == 12 and len(set(ids)) == 12
    assert len(catalogue.PROCESSES) == 8
    assert not {entry.id for entry in catalogue.NEVER_OCCUR} & set(catalogue.PROCESS_BY_ID)


def test_every_process_graph_is_closed():
    for process in catalogue.PROCESSES:
        types = [step.type for step in process.steps]
        assert len(set(types)) == len(types), process.id
        for step in process.steps:
            assert step.type in KEYWORD, f"{process.id}: {step.type} is not in the glossary"
            assert all(later in types for later in step.then), f"{process.id}: {step.type} leads nowhere"


def test_every_role_has_people_and_every_process_has_things():
    for process in catalogue.PROCESSES:
        for role in process.roles():
            assert len(catalogue.PEOPLE[role]) >= 2, role
        assert catalogue.THINGS[process.things]
        assert "{thing}" in process.item and "{number}" in process.reference


def test_every_pair_of_processes_differs():
    for one, other in combinations(catalogue.PROCESSES, 2):
        assert differ(one, other), f"{one.id} and {other.id}"


def test_lookalike_pairs_name_processes():
    for pair in catalogue.LOOKALIKES:
        assert pair[0] in catalogue.PROCESS_BY_ID and pair[1] in catalogue.PROCESS_BY_ID


def test_every_address_is_invented():
    people = [person for group in catalogue.PEOPLE.values() for person in group]
    people += [kind.sender for kind in catalogue.NOISE if kind.sender]
    assert all(person.address.endswith(".example") for person in people)


def test_every_step_type_has_templates():
    steps = load_templates()["step"]
    assert sorted(steps) == sorted(KEYWORD)
    for name, texts in steps.items():
        assert texts["subject"] and texts["with_keyword"] and texts["without_keyword"], name


def test_wordings_with_keyword_use_the_glossarys_word_and_the_others_avoid_it():
    for name, texts in load_templates()["step"].items():
        keyword = KEYWORD[name].lower()
        assert keyword in texts["subject"].lower(), name
        assert all(keyword in wording.lower() for wording in texts["with_keyword"]), name
        assert not any(keyword in wording.lower() for wording in texts["without_keyword"]), name


def test_every_kind_of_noise_has_templates():
    noise = load_templates()["noise"]
    for kind in catalogue.NOISE:
        assert noise[kind.name]["subjects"] and noise[kind.name]["texts"], kind.name
