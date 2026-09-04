"""Invariants for the published security.txt (infra this.i @qo7v2zwr).

RFC 9116 makes `Expires` mandatory, and the interesting failure is not a malformed file -- it is a
file that stays syntactically perfect while quietly becoming invalid on a date nobody diarised. A
finder who fetches an expired security.txt learns that the address may no longer be read, which is
worse than finding no file at all, because they went looking.

So the design here is a committed file plus a test that fails BEFORE it lapses, rather than a build
step that recomputes the date. A self-renewing expiry would keep promising the mailbox is monitored
long after that stopped being true, which is precisely what the field exists to communicate. The
thirty-day margin is the window in which someone confirms security@bakobo.com is still read and
moves the date by hand.

Everything here works on the committed bytes and needs no network, so it runs in the existing
test job alongside tests/test_wellknown.py.
"""

from __future__ import annotations

import datetime as dt
import difflib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SECURITY_TXT = ROOT / ".well-known" / "security.txt"
SITE = "https://bakobo.com"
RENEWAL_MARGIN = dt.timedelta(days=30)


def fields() -> dict[str, list[str]]:
    """The file's fields, comments and blank lines dropped.

    A key may legitimately repeat -- RFC 9116 allows several Contact lines -- so every value is a
    list. Reading it as a flat dict would silently keep only the last one.
    """
    found: dict[str, list[str]] = {}
    for line in SECURITY_TXT.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        name, _, value = stripped.partition(":")
        found.setdefault(name.strip().lower(), []).append(value.strip())
    return found


def expires_at() -> dt.datetime:
    """The single Expires value, or a readable assertion failure.

    Every caller is a test, and a bare KeyError from a missing field would surface as a different
    error in each of them depending on which pytest happened to run first. Failing here, once, with
    a sentence, means a malformed file produces the same message whatever the execution order.
    """
    values = fields().get("expires", [])
    assert len(values) == 1, (
        f"Expected exactly one Expires field, found {len(values)}. RFC 9116 treats a file with "
        "more than one as invalid, and one with none as incomplete."
    )
    try:
        return dt.datetime.fromisoformat(values[0].replace("Z", "+00:00"))
    except ValueError:
        raise AssertionError(
            f"Expires is {values[0]!r}, which is not an ISO 8601 timestamp. RFC 9116 requires the "
            "format from RFC 3339, e.g. 2027-08-01T00:00:00.000Z."
        ) from None


def test_the_file_is_published_at_the_path_finders_fetch():
    assert SECURITY_TXT.is_file(), (
        "security.txt must sit at /.well-known/security.txt. RFC 9116 permits a legacy location at "
        "the root, but a scanner looks under .well-known first and this is the only path worth "
        "maintaining."
    )


def test_the_contact_is_the_advertised_address():
    contacts = fields().get("contact", [])
    assert "mailto:security@bakobo.com" in contacts, (
        f"Contact must name security@bakobo.com as a mailto URI, not a bare address; found "
        f"{contacts!r}. RFC 9116 requires a URI, and a bare address is the common mistake."
    )


def test_expires_is_present_and_machine_readable():
    values = fields().get("expires", [])
    assert len(values) == 1, (
        f"Exactly one Expires field is required; found {len(values)}. RFC 9116 says a file with "
        "more than one must be treated as invalid, so a duplicate silently voids the whole file."
    )
    assert expires_at().tzinfo is not None, (
        "Expires must carry a timezone offset. A naive timestamp is ambiguous by up to a day, "
        "which is the entire margin on either side of the boundary this field defines."
    )


def test_expires_has_not_lapsed_and_is_not_about_to():
    remaining = expires_at() - dt.datetime.now(dt.timezone.utc)
    assert remaining > RENEWAL_MARGIN, (
        f"security.txt expires in {remaining.days} days. This test is the reminder: confirm that "
        "security@bakobo.com is still monitored and move the Expires date by hand. Do not extend "
        "it reflexively -- the field's whole purpose is to tell a finder that someone checked."
    )


def test_expires_is_under_a_year_out():
    remaining = expires_at() - dt.datetime.now(dt.timezone.utc)
    assert remaining < dt.timedelta(days=365), (
        f"Expires is {remaining.days} days out. RFC 9116 recommends less than a year, because the "
        "value is a claim that the address is currently read and nobody can honestly make that "
        "claim further ahead than that."
    )


def test_canonical_names_the_url_this_file_is_served_from():
    canonical = fields().get("canonical", [])
    assert canonical == [f"{SITE}/.well-known/security.txt"], (
        f"Canonical must be the published URL, found {canonical!r}. It is what lets a finder tell "
        "this file from a copy someone rehosted, and a wrong value is worse than an absent one."
    )


def test_no_field_is_empty():
    empty = [name for name, values in fields().items() if any(not v for v in values)]
    assert not empty, (
        f"These fields have no value: {empty}. A present-but-empty field parses cleanly and means "
        "nothing, which is how a missing contact address survives review."
    )


def test_the_file_is_ascii_and_uses_unix_line_endings():
    raw = SECURITY_TXT.read_bytes()
    assert b"\r" not in raw, "security.txt must use LF endings; CRLF trips some naive parsers."
    raw.decode("ascii")  # raises if not, which is the assertion


def test_no_field_name_is_a_near_miss_of_a_defined_one():
    """Catch typos without forbidding extensions.

    An earlier version of this test asserted a closed set and said RFC 9116 defines one. That is
    wrong: §4 is explicitly about extensibility and consumers must ignore fields they do not
    recognise, so a closed set here would reject a legitimate future field.

    What is still worth catching is the failure the closed set was really aimed at. A typo like
    `Contacts:` or `Expire:` does not fail — it parses as an extension field and is ignored, so the
    contact address is simply absent while the file looks fine. That is a near miss of a known
    name, which is distinguishable from a genuine extension precisely because it is nearly a known
    name. Unknown-and-unlike anything is allowed through.
    """
    defined = [
        "acknowledgments", "canonical", "contact", "encryption", "expires",
        "hiring", "policy", "preferred-languages",
    ]
    suspects = {
        name: difflib.get_close_matches(name, defined, n=1, cutoff=0.8)[0]
        for name in fields()
        if name not in defined and difflib.get_close_matches(name, defined, n=1, cutoff=0.8)
    }
    assert not suspects, (
        "These field names are one small edit from a field RFC 9116 defines, which is what a typo "
        f"looks like: {suspects}. A misspelled field is ignored rather than rejected, so the value "
        "it was carrying is silently absent."
    )
