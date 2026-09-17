"""What the deploy is allowed to publish, and that nothing else rides along (this.i @m6dofkv2).

These run the REAL stager -- `scripts/stage_site.py`, the same module the Pages workflow calls --
into a temporary directory, and assert over what it actually produced. They do not re-implement the
staging rule, and that is the point: a containment that lives only in the test suite is not
containment, and a second copy of the published list is the same drift the deny-list already had,
one level along.

The leak that earned this file: https://bakobo.com/this.i answered 200 with 16,481 bytes, carrying
all five of the terms test_site.py::test_no_stealth_leak bans. That test was not wrong -- @feshtwgl
scoped it deliberately to the two surfaces that speak about the business. The deploy staged with a
deny-list, so the published set was everything nobody had thought to exclude, and this.i was added
five days after the exclude list was written.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import stage_site  # noqa: E402


from conftest import BANNED  # noqa: E402  -- one ban, three scopes; see tests/conftest.py

# The files that leaked. Named individually, because a regression here is the exact incident
# repeating and deserves to fail by name rather than as one of N unexpected entries.
LEAKED = ("this.i", ".mcp.json")


@pytest.fixture(scope="module")
def staged(tmp_path_factory) -> Path:
    """The site as the deploy would publish it."""
    out = tmp_path_factory.mktemp("staged")
    stage_site.stage(ROOT, out)
    return out


def _relative(staged: Path) -> set[str]:
    return {str(p.relative_to(staged)) for p in staged.rglob("*") if p.is_file()}


def test_staging_into_a_dirty_destination_is_refused(tmp_path):
    """Leftovers from an earlier run would be republished alongside the allow-list.

    `copytree(dirs_exist_ok=True)` overwrites what PUBLISHED names and removes nothing else, so a
    reused `_site` makes the published set "this list, plus whatever was already there" -- the
    deny-list property @m6dofkv2 exists to remove, reintroduced by the staging step instead of the
    exclude list. CI stages into a fresh checkout so it cannot happen there today, and the leak this
    branch fixes is what "cannot happen today" is worth.
    """
    leftover = tmp_path / "this.i"
    leftover.write_text("a file a previous run published", encoding="utf-8")

    with pytest.raises(FileExistsError, match="is not empty"):
        stage_site.stage(ROOT, tmp_path)

    assert leftover.exists(), "the refusal must not delete anything it found"


def test_staging_into_a_missing_destination_is_fine(tmp_path):
    """The refusal is about leftovers, not about the directory having to pre-exist."""
    fresh = tmp_path / "nested" / "_site"
    stage_site.stage(ROOT, fresh)
    assert (fresh / "index.html").is_file()


def test_every_published_entry_exists_in_the_repo():
    """A stale entry in the allow-list is a silent hole: it names a file nobody would notice missing."""
    missing = [name for name in stage_site.PUBLISHED if not (ROOT / name).exists()]
    assert not missing, f"PUBLISHED names entries that do not exist: {missing}"


def test_nothing_outside_the_allow_list_is_staged(staged):
    allowed = set(stage_site.PUBLISHED)
    strays = sorted(
        name for name in _relative(staged)
        if name not in allowed and not any(name.startswith(f"{a}/") for a in allowed)
    )
    assert not strays, f"staged files outside PUBLISHED: {strays}"


@pytest.mark.parametrize("name", LEAKED)
def test_the_files_that_leaked_are_not_staged(staged, name):
    assert not (staged / name).exists(), (
        f"{name} is staged again. It was live on bakobo.com until 2026-09-17; see this.i @m6dofkv2."
    )


def test_the_discovery_surface_and_pages_plumbing_survive(staged):
    """The deploy's other failure mode, and the expensive one: a green deploy that 404s.

    `.well-known/` and `.nojekyll` have each been dropped by a staging step before (this.i @7vpcnhmt,
    and bakobo/schema's @o6bw3k), and an allow-list can drop them just as silently as the tar did.
    """
    for required in (".well-known/oobi", ".nojekyll", "CNAME", "index.html", "404.html"):
        assert (staged / required).exists(), f"the deploy would ship without {required}"


def test_the_social_card_source_is_not_staged(staged):
    """assets/ ships; assets/social is the card generator's working tree and speaks about the business."""
    assert (staged / "assets").is_dir()
    assert not (staged / "assets" / "social").exists()


def test_no_staged_text_file_breaks_stealth(staged):
    """@feshtwgl over the whole published tree rather than two hand-named files.

    .well-known/ is exempt exactly as @feshtwgl says -- there the terms are the payload, and that
    exemption is a decision rather than an oversight.
    """
    offenders = []
    for path in sorted(staged.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(staged)
        if relative.parts and relative.parts[0] == ".well-known":
            continue
        try:
            body = path.read_text(encoding="utf-8").lower()
        except (UnicodeDecodeError, OSError):
            continue
        for banned in BANNED:
            if banned in body:
                offenders.append(f"{relative}: {banned!r}")
    assert not offenders, f"stealth leak in the staged site: {offenders}"


def test_the_workflow_calls_this_stager_rather_than_staging_its_own_way():
    """The join between the workflow and the allow-list, asserted where it can drift.

    Without this, the workflow could go back to an rsync and every test above would still pass --
    which is how the published set and the stealth rule got out of step in the first place.
    """
    workflow = (ROOT / ".github" / "workflows" / "pages.yml").read_text(encoding="utf-8")

    # COMMENTS STRIPPED BEFORE EITHER ASSERTION, and the first one is why this comment exists.
    #
    # The original version of this test asserted `"scripts/stage_site.py" in workflow` against the
    # raw text -- which the step's own explanatory comment satisfies, so the deploy could stop
    # calling the stager entirely and this test would still pass. Copilot caught it on PR #13. It
    # is the same bug as the rsync check three lines down, which had already been fixed for the
    # same reason, two lines apart, in the same sitting. Worth leaving written down: a fix applied
    # to one assertion does not travel to its neighbour on its own.
    code = [line.split("#", 1)[0] for line in workflow.splitlines()]

    assert any("scripts/stage_site.py" in line for line in code), (
        "no executable line in the Pages workflow calls the stager"
    )

    invocations = [line for line in code if "rsync" in line]
    assert not invocations, f"the Pages workflow still stages with rsync (a deny-list): {invocations}"
