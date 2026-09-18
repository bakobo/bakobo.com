#!/usr/bin/env python3
"""Stage the publishable site into a directory, from an ALLOW-list (this.i @m6dofkv2).

Usage: python3 scripts/stage_site.py <destination>

The Pages workflow calls this, and tests/test_publish_set.py imports it and runs it. One name, one
place -- a second copy of the published set is the same drift the deny-list had, one level along.

WHY AN ALLOW-LIST, stated here because the deny-list looked completely reasonable for months.

The deploy used to stage with `rsync --exclude=...` over the whole repository, which makes the
published set "everything nobody thought to exclude". That fails open on every file added after the
list was written, it fails silently, and it is invisible from inside the repo because everything
works for anyone who already has the whole tree. On 2026-09-17 https://bakobo.com/this.i answered 200
with 16,481 bytes, carrying all five of the terms @feshtwgl bans; /.mcp.json was live beside it.
this.i had been added five days after that exclude list.

An allow-list fails the other way. A new file is unpublished until somebody names it here, and the
failure mode is a missing page -- loud, immediate, and fixed by one line.

THE LIST IS TOP-LEVEL, and that promise is narrower than it first reads. An entry naming a directory
publishes its whole subtree, so a file dropped into assets/ or .well-known/ ships without anybody
naming it, and PRUNED below is the only thing that keeps something down there off the site. Both of
those trees are generated or curated one file at a time, which is why they are trusted wholesale.
Do not add a directory entry for a tree people drop files into casually -- inside such a tree the
deny-list property this list exists to remove is back, one level down.

WHAT IS NOT HERE, and must not be added without reading @feshtwgl and @m6dofkv2 first: this.i,
.mcp.json, AGENTS.md, CLAUDE.md, GEMINI.md, .cursorrules, README.md, tests/, scripts/, .tick/,
.github/, pyproject.toml, uv.lock. Each of those either speaks about the business or describes how
the estate is built, and neither belongs on a placeholder whose whole job is to reveal nothing.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

# Every path published at https://bakobo.com/, relative to the repository root. A directory publishes
# its whole subtree, minus PRUNED below.
#
# The four community files were already served before this list existed and stay, deliberately:
# dropping four live URLs is a separate decision from closing a leak, and bundling them would hide
# the leak. Revisit them on their own merits, not as part of this change.
PUBLISHED: tuple[str, ...] = (
    # Pages plumbing. Each has been silently dropped by a staging step before -- see @7vpcnhmt and
    # bakobo/schema's @o6bw3k -- and the failure is a green deploy serving a 404.
    ".nojekyll",
    "CNAME",
    # The site itself.
    "index.html",
    "404.html",
    "assets",
    "favicon.ico",
    "robots.txt",
    "sitemap.xml",
    # The machine-readable directory. @feshtwgl puts this deliberately outside the stealth ban:
    # here the terms are the payload.
    ".well-known",
    # Community files, already live before this list. See the note above.
    "CODE_OF_CONDUCT.md",
    "CONTRIBUTING.md",
    "COPYRIGHT.md",
    "SECURITY.md",
)

# Subtrees inside a published directory that do not ship.
#
# assets/social holds the card GENERATOR's working copy -- card.html carries the business copy that
# test_no_stealth_leak scans precisely because it is not meant to be reachable. The rendered card it
# produces is assets/img/og-card.png, which does ship.
PRUNED: frozenset[str] = frozenset({"assets/social"})

# Never staged from anywhere, whatever the allow-list says. These appear inside published
# directories only by accident of a local run, and shipping one is pure noise.
PRUNED_NAMES: frozenset[str] = frozenset({"__pycache__", ".pytest_cache", ".DS_Store"})


def _ignore(directory: str, names: list[str]) -> set[str]:
    """shutil.copytree's filter: prune by name anywhere, and by path where PRUNED says so."""
    here = Path(directory)
    dropped = {name for name in names if name in PRUNED_NAMES}
    for name in names:
        try:
            relative = (here / name).relative_to(_ignore.root)  # type: ignore[attr-defined]
        except ValueError:
            continue
        if relative.as_posix() in PRUNED:
            dropped.add(name)
    return dropped


def stage(root: Path, destination: Path) -> list[str]:
    """Copy every PUBLISHED entry from ``root`` into ``destination``. Returns what was staged.

    Raises FileNotFoundError if the allow-list names something that is not there. A stale entry is a
    silent hole -- it names a file nobody would notice missing -- so it fails rather than warns.
    """
    root = root.resolve()

    # A NON-EMPTY DESTINATION IS REFUSED, and this is not fussiness.
    #
    # `copytree(dirs_exist_ok=True)` overwrites the paths PUBLISHED names and removes nothing else,
    # so staging into a directory a previous run left behind republishes whatever that run put
    # there -- including a file since removed from the allow-list. That is the deny-list failure
    # wearing a different hat: the published set becomes "this list, plus whatever was already
    # lying around", which is exactly the property @m6dofkv2 exists to remove. CI stages into a
    # fresh checkout so it cannot happen there today, and "cannot happen today" is how the last
    # one got in.
    if destination.exists() and any(destination.iterdir()):
        raise FileExistsError(
            f"stage_site: {destination} is not empty. Staging into it would publish leftovers from "
            "an earlier run alongside the allow-list. Remove it first; the output must be a fresh "
            "projection of PUBLISHED and nothing else."
        )

    destination.mkdir(parents=True, exist_ok=True)
    _ignore.root = root  # type: ignore[attr-defined]

    staged: list[str] = []
    for name in PUBLISHED:
        source = root / name
        if not source.exists():
            raise FileNotFoundError(
                f"stage_site: PUBLISHED names {name!r}, which does not exist in {root}. "
                "Remove it from the list or restore the file -- a stale entry publishes nothing "
                "and reads as though it does."
            )
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        if source.is_dir():
            shutil.copytree(source, target, ignore=_ignore, dirs_exist_ok=True)
        else:
            shutil.copy2(source, target)
        staged.append(name)
    return staged


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__.splitlines()[2], file=sys.stderr)
        return 2
    root = Path(__file__).resolve().parent.parent
    staged = stage(root, Path(argv[1]))
    print(f"staged {len(staged)} entries into {argv[1]}: {', '.join(staged)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
