"""Invariants for the published .well-known discovery surface (this.i @7vpcnhmt).

The tree is generated in bakobo/infra and committed here (@klykqkst), so what these checks are for
is the gap that arrangement creates: between the generator running and this repo deploying, the
files are just files, and a bad merge or a hand-edit would publish a directory of identifiers that
nobody re-derived. Everything here works on the committed bytes and needs no network, so it runs in
the existing test job. The one thing it cannot see -- whether a witness still serves what we
published -- is scripts/check_wellknown_live.py, on a schedule.

The strongest check here is that a witness AID is re-proved from its own event rather than read out
of the catalog. A non-transferable AID *is* its signing key, so the committed OOBI proves the
directory name it sits in, and no amount of editing the catalog can fake that.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WELL_KNOWN = ROOT / ".well-known"
OOBI_DIR = WELL_KNOWN / "oobi"
SITE = "https://bakobo.com"
WITNESS_AID = re.compile(r"^B[A-Za-z0-9_-]{43}$")


def catalog() -> dict:
    return json.loads((OOBI_DIR / "index.json").read_text())


def published_aids() -> list[str]:
    return sorted(p.name for p in OOBI_DIR.iterdir() if p.is_dir())


def leading_event(body: bytes) -> dict:
    """The KERI event at the head of a CESR stream."""
    event, _ = json.JSONDecoder().raw_decode(body.decode("utf-8"))
    return event


# --- the contract GLEIF defines -------------------------------------------

def test_host_meta_is_a_jrd_for_this_origin():
    jrd = json.loads((WELL_KNOWN / "host-meta.json").read_text())
    assert jrd["subject"] == SITE
    rels = {link["rel"]: link for link in jrd["links"]}
    assert rels[f"{SITE}/rels/oobi"]["template"] == f"{SITE}/.well-known/oobi/{{said}}/index.json"
    assert rels[f"{SITE}/rels/discovery-catalog"]["href"] == f"{SITE}/.well-known/oobi/index.json"


def test_host_meta_subject_matches_the_cname():
    """A host-meta advertising the wrong origin sends every client somewhere we do not serve."""
    jrd = json.loads((WELL_KNOWN / "host-meta.json").read_text())
    assert jrd["subject"] == f"https://{(ROOT / 'CNAME').read_text().strip()}"


def test_catalog_and_directories_are_the_same_set():
    """An orphan directory is an identifier we serve but never announced, and vice versa."""
    listed = {aid for group in catalog()["resources"].values() for aid in group}
    assert listed == set(published_aids())


def test_catalog_count_matches_what_is_published():
    assert catalog()["count"] == len(published_aids())


def test_every_catalog_entry_resolves_to_a_file():
    for group in catalog()["resources"].values():
        for aid, entry in group.items():
            assert entry["oobi"] == f"/.well-known/oobi/{aid}/index.json"
            assert (ROOT / entry["oobi"].lstrip("/")).is_file()


# --- the identifiers prove themselves -------------------------------------

def test_every_published_oobi_proves_the_aid_it_is_filed_under():
    for aid in published_aids():
        event = leading_event((OOBI_DIR / aid / "index.json").read_bytes())
        assert event["t"] == "icp", f"{aid} is filed under a {event['t']} event"
        assert event["i"] == aid, f"{aid} contains an event for {event['i']}"
        assert event["k"] == [aid], f"{aid} is not the sole signing key of its own event"


def test_every_witness_is_non_transferable():
    """A rotatable key would mean the AID stops proving the key, so the file stops proving anything."""
    for aid in published_aids():
        event = leading_event((OOBI_DIR / aid / "index.json").read_bytes())
        assert WITNESS_AID.fullmatch(aid)
        assert event["nt"] in (0, "0")
        assert event["n"] == []


def test_published_bodies_keep_their_cesr_attachment():
    """Byte-exactness matters because these are signed; a bare JSON body means someone reserialised."""
    for aid in published_aids():
        body = (OOBI_DIR / aid / "index.json").read_bytes()
        _, offset = json.JSONDecoder().raw_decode(body.decode("utf-8"))
        assert body[offset:].startswith(b"-"), f"{aid} has no CESR attachment after the event"


# --- what we say about it -------------------------------------------------

def test_catalog_states_the_availability_limitation():
    """this.i @lbk6u4ru: a machine client gets the qualification too, not just a human reader."""
    described = catalog()["description"].lower()
    assert "availability" in described
    assert "controller-accountability" in described


def test_landing_page_states_the_limitation_and_points_at_no_third_party():
    page = (WELL_KNOWN / "index.html").read_text().lower()
    assert "availability" in page
    assert "controller-accountability" in page
    assert "gleif" not in page          # this.i @v7rjsabf
    assert "schema.bakobo.com" in page  # this.i @7ufzxzip


def test_no_schemas_are_re_served_here():
    """this.i @7ufzxzip: schemas live at schema.bakobo.com, not in a second copy on the apex."""
    assert set(catalog()["resources"]) == {"witness"}


def test_the_surface_is_marked_generated():
    assert "do not edit by hand" in (WELL_KNOWN / "index.html").read_text().lower()
    assert catalog()["generator"].startswith("bakobo/infra")


# --- the stealth boundary this endpoint moved (this.i @feshtwgl) ----------

def test_the_placeholder_still_says_nothing_about_the_stack():
    """@feshtwgl narrowed stealth to product strategy; it did not remove it from index.html."""
    haystack = " ".join(
        (ROOT / p).read_text().lower() for p in ("index.html", "assets/social/card.html")
    )
    for banned in ("sedi", "keri", "acdc", "utah", "reissuer"):
        assert banned not in haystack


def test_the_discovery_surface_is_not_linked_from_the_placeholder():
    """The endpoint is for machines that come looking, not an announcement on the front page."""
    assert ".well-known" not in (ROOT / "index.html").read_text()


def test_the_landing_page_asks_not_to_be_indexed():
    """A trust surface should be resolvable, not promoted into search results."""
    assert 'name="robots" content="noindex"' in (WELL_KNOWN / "index.html").read_text()


# --- host-meta-v2: our additions, which must stay ignorable ---------------

def v2() -> dict:
    return json.loads((WELL_KNOWN / "host-meta-v2.json").read_text())


def test_v2_delegation_declares_that_it_conveys_no_trust():
    """this.i @bio6glms. Silence here would be read as the stronger claim."""
    doc = v2()
    assert doc["delegations"]
    for d in doc["delegations"]:
        assert d["strength"] == "hint"
    assert "no trust" in doc["delegationNote"].lower()


def test_v2_points_at_the_schema_registry_rather_than_re_serving_it():
    """this.i @7ufzxzip: schemas stay at their own origin; the apex only indicates them."""
    hrefs = [d["href"] for d in v2()["delegations"]]
    assert "https://schema.bakobo.com/" in hrefs
    assert set(catalog()["resources"]) == {"witness"}


def test_v1_host_meta_carries_no_trace_of_v2():
    """@sv6rtl3k: a consumer that has never heard of v2 must see an unchanged contract."""
    v1 = json.loads((WELL_KNOWN / "host-meta.json").read_text())
    assert set(v1) == {"subject", "links"}
    blob = json.dumps(v1)
    assert "delegat" not in blob and "strength" not in blob


def test_external_lists_a_directory_and_republishes_no_identifier():
    """this.i @6koo6gff: point at their catalog, never copy its contents."""
    doc = v2()
    assert doc["external"]
    for e in doc["external"]:
        assert e["strength"] == "hint"
        assert e["catalog"].startswith("https://")
    blob = json.dumps(doc)
    for foreign in ("BDkq35LUU63xnFmfhljYYRY0ymkCg7goyeCxN30tsvmS",
                    "EDP1vHcw_wc4M__Fj53-cJaBnZZASd-aMTaSyWEQ-PC2"):
        assert foreign not in blob


def test_external_disclaims_operation_and_relationship():
    note = v2()["externalNote"].lower()
    assert "no trust" in note
    assert "does not operate" in note
    assert "no relationship" in note


# --- the deploy actually ships the dot-directory --------------------------

def test_the_pages_workflow_does_not_use_upload_pages_artifact():
    """It tars with --exclude=".[^/]*", which silently drops .well-known and .nojekyll.

    The failure mode is the dangerous kind: the deploy goes green, the site looks fine, and the
    discovery endpoint 404s. It cost this repo one live deploy, and bakobo/schema one before that
    (its this.i @o6bw3k). The action offers no way to turn the exclusion off, so the only fix is
    not to use it -- which makes its absence the thing worth asserting.
    """
    workflow = (ROOT / ".github" / "workflows" / "pages.yml").read_text()
    used = re.findall(r"^\s*(?:-\s*)?uses:\s*(\S+)", workflow, re.M)
    assert not any("upload-pages-artifact" in action for action in used), used


def test_the_pages_artifact_keeps_hidden_files():
    """actions/upload-artifact drops dotfiles unless told otherwise, for the same net effect."""
    workflow = (ROOT / ".github" / "workflows" / "pages.yml").read_text()
    assert "include-hidden-files" in workflow
    assert "github-pages" in workflow  # deploy-pages only consumes an artifact of this name


def test_the_deploy_does_not_exclude_the_discovery_surface():
    """`scripts` and `tests` are excluded from the published site; `.well-known` must not be."""
    workflow = (ROOT / ".github" / "workflows" / "pages.yml").read_text()
    assert "--exclude='.well-known'" not in workflow
    assert "--exclude='scripts'" in workflow
