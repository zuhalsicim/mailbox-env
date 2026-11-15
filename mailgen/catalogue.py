"""SAMPLE CONTENT, TO BE REPLACED BY THE AUTHOR.

The company, its people, the glossary of step types, the eight processes and
the four catalogue entries that never occur. Everything in this file is data;
the engine reads it and knows nothing about the company itself. All names,
firms and places are invented, and every mail address ends in ".example".
"""

from mailgen.model import CatalogueEntry, NoiseKind, Person, Process, Step, StepType

COMPANY = "Halden & Roth Messtechnik GmbH"
PLACE = "Neuwerder"
DOMAIN = "halden-roth.example"
DEPARTMENTS = ("Einkauf", "Vertrieb", "Buchhaltung", "Personal", "IT", "Qualität", "Wareneingang", "Leitung")


def _people(domain: str, *names: str) -> list[Person]:
    return [Person(name, name.lower().replace(" ", ".") + "@" + domain) for name in names]


_PARTNERS = (
    _people("limeta-sensorik.example", "Bernd Tiemann")
    + _people("varnow-regeltechnik.example", "Lea Winkel")
    + _people("sandrup-feinmechanik.example", "Rolf Jansen")
    + _people("quellwerk-elektronik.example", "Dana Scholl")
    + _people("ostheide-kalibrierdienst.example", "Timo Aumann")
    + _people("tellmann-griep.example", "Sara Brix")
)

# Who can play which role. A role is a department, a kind of outsider, or "Mitarbeiter"
# for whoever asks for something. Suppliers and customers are the same firms on purpose.
PEOPLE = {
    "Einkauf": _people(DOMAIN, "Jana Wolff", "Tobias Brandl", "Merle Kessin"),
    "Vertrieb": _people(DOMAIN, "Henrik Sauer", "Carla Mertens", "Dennis Vogt"),
    "Buchhaltung": _people(DOMAIN, "Ingrid Pohl", "Marek Stein", "Selma Kurz"),
    "Personal": _people(DOMAIN, "Ruth Lindner", "Oliver Hartwig", "Nadine Graf"),
    "IT": _people(DOMAIN, "Sven Marder", "Aylin Berg", "Jonas Reich"),
    "Qualität": _people(DOMAIN, "Petra Holm", "Felix Dorn", "Elif Tanner"),
    "Wareneingang": _people(DOMAIN, "Uwe Kranz", "Mira Stolz", "Pavel Rink"),
    "Leitung": _people(DOMAIN, "Gerda Roth", "Martin Halden", "Simone Voigt"),
    "Lieferant": _PARTNERS,
    "Kunde": _PARTNERS,
    "Bewerber": _people("post.example", "Lukas Ferber", "Emre Aksoy")
    + _people("mailhaus.example", "Hannah Zeisig", "Paula Rensing"),
    "Reisebüro": _people("fernblick-reisen.example", "Katrin Lohse", "Milan Brecht"),
}
PEOPLE["Mitarbeiter"] = (
    PEOPLE["Einkauf"] + PEOPLE["Vertrieb"] + PEOPLE["Qualität"] + PEOPLE["Wareneingang"] + PEOPLE["IT"]
)

# The glossary: the closed list of step types, with the word the glossary uses for each.
STEP_TYPES = (
    StepType("ABLEHNUNG", "Ablehnung", "Ein Antrag wird abgelehnt."),
    StepType("ABRECHNUNG", "Abrechnung", "Jemand reicht nach einer Reise die Kosten zur Erstattung ein."),
    StepType("ABSAGE", "Absage", "Einer Bewerberin oder einem Bewerber wird mitgeteilt, dass es mit der Stelle nichts wird."),
    StepType("ANFRAGE", "Anfrage", "Jemand fragt, ob und zu welchem Preis etwas geliefert werden kann."),
    StepType("ANGEBOT", "Angebot", "Jemand nennt Preis und Bedingungen für eine Lieferung."),
    StepType("ANTRAG", "Antrag", "Jemand bittet um etwas, das genehmigt werden muss."),
    StepType("AUFTRAGSBESTAETIGUNG", "Auftragsbestätigung", "Der Verkäufer bestätigt, dass er eine Bestellung angenommen hat."),
    StepType("BEDARF", "Bedarf", "Eine Abteilung meldet, dass sie etwas braucht."),
    StepType("BESTAETIGUNG", "Bestätigung", "Jemand bestätigt, dass etwas Eingerichtetes funktioniert."),
    StepType("BESTELLUNG", "Bestellung", "Jemand bestellt verbindlich eine Ware oder Leistung."),
    StepType("BEWERBUNG", "Bewerbung", "Jemand bewirbt sich auf eine Stelle."),
    StepType("BUCHUNG", "Buchung", "Das Reisebüro meldet, dass Fahrt und Unterkunft gebucht sind."),
    StepType("EINLADUNG", "Einladung", "Eine Bewerberin oder ein Bewerber wird zum Gespräch eingeladen."),
    StepType("EINRICHTUNG", "Einrichtung", "Die IT meldet, dass ein Zugang eingerichtet ist."),
    StepType("ERSATZLIEFERUNG", "Ersatzlieferung", "Der Verkäufer kündigt an, mangelhafte Ware zu ersetzen."),
    StepType("FREIGABE", "Freigabe", "Eine Vorgesetzte oder ein Vorgesetzter genehmigt etwas."),
    StepType("GUTSCHRIFT", "Gutschrift", "Der Verkäufer schreibt dem Käufer einen Betrag gut."),
    StepType("LIEFERMELDUNG", "Liefermeldung", "Jemand meldet, dass Ware unterwegs oder angekommen ist."),
    StepType("MAENGELANZEIGE", "Mängelanzeige", "Im Haus wird gemeldet, dass gelieferte Ware Mängel hat."),
    StepType("MAHNUNG", "Mahnung", "Jemand erinnert an eine offene Rechnung."),
    StepType("MELDUNG", "Meldung", "Eine Entscheidung über einen Antrag wird der Personalabteilung gemeldet."),
    StepType("PRUEFUNG", "Prüfung", "Die Qualitätsabteilung berichtet, was sie an einer beanstandeten Lieferung gefunden hat."),
    StepType("RECHNUNG", "Rechnung", "Jemand stellt einen Betrag in Rechnung."),
    StepType("REKLAMATION", "Reklamation", "Ein Käufer beanstandet eine Lieferung beim Verkäufer."),
    StepType("RUECKMELDUNG", "Rückmeldung", "Die Fachabteilung sagt nach dem Gespräch, was sie von der Bewerbung hält."),
    StepType("STELLUNGNAHME", "Stellungnahme", "Der Verkäufer nimmt zu einer Beanstandung Stellung."),
    StepType("WEITERLEITUNG", "Weiterleitung", "Unterlagen werden an die zuständige Abteilung weitergegeben."),
    StepType("ZAHLUNG", "Zahlung", "Jemand teilt mit, dass ein Betrag überwiesen wurde."),
    StepType("ZUSAGE", "Zusage", "Einer Bewerberin oder einem Bewerber wird die Stelle zugesagt."),
)

# The things cases are about. A process names its list and says how a mail phrases the thing.
THINGS = {
    "Waren": [
        "Drucksensor PS-200",
        "Temperaturfühler TF-12",
        "Kalibriergewicht 500 g",
        "Messverstärker MV-4",
        "Dichtungssatz DS-8",
        "Prüfadapter PA-31",
    ],
    "Urlaub": ["vom 12.05. bis 23.05.", "vom 02.06. bis 06.06.", "am 20.06.", "vom 14.07. bis 01.08."],
    "Reisen": [
        "nach Lindhafen zur Kundenabnahme",
        "nach Torbrück zur Fachmesse",
        "nach Selmried zur Schulung beim Lieferanten",
    ],
    "Stellen": ["Servicetechnik Außendienst", "Sachbearbeitung Einkauf", "Prüffeldmechanik", "Vertriebsinnendienst"],
}

PROCESSES = (
    Process(
        id="K01",
        name="Beschaffung",
        matter="Das Unternehmen kauft Ware oder eine Leistung bei einem Lieferanten.",
        things="Waren",
        item="{thing}",
        reference="B-{number}",
        steps=(
            Step("BEDARF", "Mitarbeiter", "Einkauf", then=("ANGEBOT", "BESTELLUNG")),
            Step("ANGEBOT", "Lieferant", "Einkauf", then=("FREIGABE",)),
            Step("FREIGABE", "Leitung", "Einkauf", then=("BESTELLUNG",)),
            Step("BESTELLUNG", "Einkauf", "Lieferant", then=("LIEFERMELDUNG",)),
            Step("LIEFERMELDUNG", "Wareneingang", "Einkauf", then=("RECHNUNG",)),
            Step("RECHNUNG", "Lieferant", "Buchhaltung", then=("ZAHLUNG", "MAHNUNG")),
            Step("MAHNUNG", "Lieferant", "Buchhaltung", then=("ZAHLUNG",)),
            Step("ZAHLUNG", "Buchhaltung", "Lieferant"),
        ),
    ),
    Process(
        id="K03",
        name="Kundenauftrag",
        matter="Ein Kunde kauft Ware beim Unternehmen.",
        things="Waren",
        item="{thing}",
        reference="A-{number}",
        steps=(
            Step("ANFRAGE", "Kunde", "Vertrieb", then=("ANGEBOT",)),
            Step("ANGEBOT", "Vertrieb", "Kunde", then=("BESTELLUNG",)),
            Step("BESTELLUNG", "Kunde", "Vertrieb", then=("AUFTRAGSBESTAETIGUNG",)),
            Step("AUFTRAGSBESTAETIGUNG", "Vertrieb", "Kunde", then=("LIEFERMELDUNG",)),
            Step("LIEFERMELDUNG", "Vertrieb", "Kunde", then=("RECHNUNG",)),
            Step("RECHNUNG", "Buchhaltung", "Kunde", then=("ZAHLUNG", "MAHNUNG")),
            Step("MAHNUNG", "Buchhaltung", "Kunde", then=("ZAHLUNG",)),
            Step("ZAHLUNG", "Kunde", "Buchhaltung"),
        ),
    ),
    Process(
        id="K04",
        name="Reklamation beim Lieferanten",
        matter="Das Unternehmen beanstandet eine Lieferung bei einem Lieferanten.",
        things="Waren",
        item="{thing}",
        reference="B-{number}",
        steps=(
            Step("MAENGELANZEIGE", "Wareneingang", "Einkauf", then=("REKLAMATION",)),
            Step("REKLAMATION", "Einkauf", "Lieferant", then=("STELLUNGNAHME",)),
            Step("STELLUNGNAHME", "Lieferant", "Einkauf", then=("GUTSCHRIFT", "ERSATZLIEFERUNG")),
            Step("GUTSCHRIFT", "Lieferant", "Buchhaltung"),
            Step("ERSATZLIEFERUNG", "Lieferant", "Einkauf"),
        ),
    ),
    Process(
        id="K06",
        name="Kundenreklamation",
        matter="Ein Kunde beanstandet eine Lieferung des Unternehmens.",
        things="Waren",
        item="{thing}",
        reference="A-{number}",
        steps=(
            Step("REKLAMATION", "Kunde", "Vertrieb", then=("PRUEFUNG",)),
            Step("PRUEFUNG", "Qualität", "Vertrieb", then=("STELLUNGNAHME",)),
            Step("STELLUNGNAHME", "Vertrieb", "Kunde", then=("GUTSCHRIFT", "ERSATZLIEFERUNG")),
            Step("GUTSCHRIFT", "Buchhaltung", "Kunde"),
            Step("ERSATZLIEFERUNG", "Vertrieb", "Kunde"),
        ),
    ),
    Process(
        id="K07",
        name="Urlaubsantrag",
        matter="Jemand aus der Belegschaft möchte Urlaub nehmen.",
        things="Urlaub",
        item="Urlaub {thing}",
        reference="U-{number}",
        steps=(
            Step("ANTRAG", "Mitarbeiter", "Leitung", then=("FREIGABE", "ABLEHNUNG")),
            Step("FREIGABE", "Leitung", "Mitarbeiter", then=("MELDUNG",)),
            Step("ABLEHNUNG", "Leitung", "Mitarbeiter", then=("MELDUNG",)),
            Step("MELDUNG", "Leitung", "Personal"),
        ),
    ),
    Process(
        id="K09",
        name="Dienstreise",
        matter="Jemand aus der Belegschaft reist im Auftrag des Unternehmens.",
        things="Reisen",
        item="Dienstreise {thing}",
        reference="R-{number}",
        steps=(
            Step("ANTRAG", "Mitarbeiter", "Leitung", then=("FREIGABE",)),
            Step("FREIGABE", "Leitung", "Mitarbeiter", then=("BUCHUNG",)),
            Step("BUCHUNG", "Reisebüro", "Mitarbeiter", then=("ABRECHNUNG",)),
            Step("ABRECHNUNG", "Mitarbeiter", "Buchhaltung", then=("ZAHLUNG",)),
            Step("ZAHLUNG", "Buchhaltung", "Mitarbeiter"),
        ),
    ),
    Process(
        id="K10",
        name="Einstellung",
        matter="Das Unternehmen besetzt eine Stelle mit einer Bewerberin oder einem Bewerber.",
        things="Stellen",
        item="die Stelle {thing}",
        reference="S-{number}",
        steps=(
            Step("BEWERBUNG", "Bewerber", "Personal", then=("WEITERLEITUNG",)),
            Step("WEITERLEITUNG", "Personal", "Leitung", then=("EINLADUNG", "ABSAGE")),
            Step("EINLADUNG", "Personal", "Bewerber", then=("RUECKMELDUNG",)),
            Step("RUECKMELDUNG", "Leitung", "Personal", then=("ZUSAGE", "ABSAGE")),
            Step("ZUSAGE", "Personal", "Bewerber"),
            Step("ABSAGE", "Personal", "Bewerber"),
        ),
    ),
    Process(
        id="K12",
        name="IT-Zugang",
        matter="Für eine Stelle wird ein Zugang zu den IT-Systemen eingerichtet.",
        things="Stellen",
        item="IT-Zugang für die Stelle {thing}",
        reference="T-{number}",
        steps=(
            Step("ANTRAG", "Personal", "Leitung", then=("FREIGABE",)),
            Step("FREIGABE", "Leitung", "IT", then=("EINRICHTUNG",)),
            Step("EINRICHTUNG", "IT", "Personal", then=("BESTAETIGUNG",)),
            Step("BESTAETIGUNG", "Personal", "IT"),
        ),
    ),
)
PROCESS_BY_ID = {process.id: process for process in PROCESSES}

# In the catalogue the agent reads, but never in a mailbox: the catalogue cannot be copied as the answer.
NEVER_OCCUR = (
    CatalogueEntry("K02", "Inventur", "Das Unternehmen zählt seinen Lagerbestand."),
    CatalogueEntry("K05", "Schulung", "Jemand aus der Belegschaft nimmt an einer Weiterbildung teil."),
    CatalogueEntry("K08", "Vertragsverlängerung", "Ein laufender Vertrag mit einem Geschäftspartner wird verlängert."),
    CatalogueEntry("K11", "Angebotsanfrage ohne Auftrag", "Das Unternehmen holt Preise ein, ohne danach zu bestellen."),
)
CATALOGUE = sorted(
    [CatalogueEntry(process.id, process.name, process.matter) for process in PROCESSES] + list(NEVER_OCCUR),
    key=lambda entry: entry.id,
)

# Pairs of processes that are easy to mix up. On the higher levels some of them share people and things.
LOOKALIKES = (
    ("K01", "K03"),  # buying and selling the same goods
    ("K01", "K04"),  # an order and the complaint about it
    ("K04", "K06"),  # complaints with mirrored roles
    ("K07", "K09"),  # both start with ANTRAG and FREIGABE
    ("K01", "K09"),  # both end with money going out
    ("K10", "K12"),  # the same new position
    ("K07", "K12"),  # both start with ANTRAG and FREIGABE
)

NOISE = (
    NoiseKind("messe", sender=Person("Fachmesse Sensorik", "newsletter@fachmesse-sensorik.example")),
    NoiseKind("kantine", sender=Person("Kantine", "kantine@" + DOMAIN)),
    NoiseKind("abwesenheit", auto_reply=True),
    NoiseKind("geburtstag"),
    NoiseKind("phishing", sender=Person("Postfach-Service", "service@postfach-pruefung.example")),
)
