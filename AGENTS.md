## Testing Protocol

This repo has a test suite: `pytest`, standard-library only, in `tests/` (see
the README for how to run it). It checks the invariants that quietly break a
static placeholder — every referenced asset resolves, the canonical/OG/JSON-LD
metadata is present and valid, the social card is exactly 1200×630, robots.txt
stays a pure signal, and no stealth-leak terms appear in the published copy.

Keep it green, and grow it with the site:

- Run `pytest` before every commit; never check in with the suite red.
- When you add or change a feature — a page, an asset, an SEO/metadata rule, a
  workflow — add or update a check that would fail without your change. For
  logic with real branches, prefer writing the failing check first (TDD).
- When you change the site's public promise (what it may or may not reveal),
  encode it as a test (see `test_no_stealth_leak`) so the boundary can't erode.

This is a content/brand site, not an app, so chase *meaningful* coverage of
behavior and invariants rather than a line-coverage number.

## CI and Documentation

CI lives in `.github/workflows/pages.yml`: it runs the test suite on every push
and pull request, and deploys to GitHub Pages from `main` once tests pass. A
second workflow, `.github/workflows/wellknown-drift.yml`, runs daily and on pull
requests that touch `.well-known/`; it re-fetches every published OOBI and fails
if the committed bytes no longer match what the witness serves. It is separate
from the deploy on purpose — it needs network to four hosts on three continents,
and a restarting witness must not fail an unrelated deploy. The `README.md`
carries both status badges and the fresh-clone-to-passing-tests steps; keep them
current as the site evolves.

## The `.well-known/` tree is generated — never hand-edit it, with one named exception

`security.txt` is the exception, and it is the only one. It is hand-maintained here on purpose:
RFC 9116's mandatory `Expires` field is a claim that a human still reads the address, so the date
is committed and `tests/test_security_txt.py` fails thirty days before it lapses. Generating it
would move that date into a generator and further from the test that guards it, and a
self-renewing expiry would keep asserting the mailbox is monitored after that stopped being true —
which is the one thing the field exists to communicate (infra `@qo7v2zwr`). The generator does not
touch it: it rebuilds only `.well-known/oobi/`, which is the sole subtree it removes
(`wellknown/gen_wellknown.py:472` in `bakobo/infra`), and infra's own suite asserts that a
pre-existing `security.txt` survives a run.

Everything else under `.well-known/` is build output from `wellknown/bin/gen-wellknown`
in the **private `bakobo/infra` repo**, which reads the witness hostnames from
OpenTofu state and each AID from the inception event that witness serves. If you
need to change what is published, change the generator there and regenerate; a
fix applied here is overwritten on the next run and, worse, breaks the byte-exact
copy the OOBI signatures depend on. The reasoning is in `this.i` — `@mwa7fvu6`
(nothing hand-typed), `@klykqkst` (why the generator is in the other repo), and
`@lbk6u4ru` (why the published wording says availability rather than
accountability, and why it needs Daniel's approval before it changes).

When writing or modifying GitHub Actions workflows, always use the latest
stable release of each action. Avoid versions pinned to Node.js 16 or
Node.js 20 (both deprecated by GitHub). In 2026, this meant to prefer Node.js
24-compatible versions, but the standard may evolve over time. Check the GitHub
Marketplace for each action's current release.

<!-- >>> tick stanza >>> (managed by `tick init`) -->

## Task tracking: `tick`

This repo tracks tasks, tech debt, and ideas in a local [`tick`](https://github.com/dhh1128/tick)
ledger (an orphan `tick` branch; the `tick` CLI is the interface). Reads are plain
files — do **not** use an external API for task tracking.

- **First, if a `tick` command says the repo isn't initialized**, run `tick init`
  once to connect this clone to the ledger — it adopts the existing remote ledger
  if a colleague already set one up, or creates a new one otherwise.
- **A tick mark is the sigil `~` immediately followed by a digit-first 4-char
  base32 id** (the id part looks like `4mz3`, so the full mark is that id with a
  leading `~`). It pins a tick to a code location.
- **Before editing a file**, grep it for marks and read what they reference:
  `rg '~[2-7][a-z2-7]{3}\b' <file>` then `tick show <id>`. A mark means recorded
  context exists for that spot — read it first.
- **Search** existing ticks with `tick grep <text>`; **list** with `tick ls`.
- **Capture** new work with `tick add "<title>"` and place the printed mark
  (`~` + the new id) at the relevant code spot.
- When your change **resolves** a tick, run `tick off <id>` and **delete the
  mark(s)** it reports still in the code.

<!-- <<< tick stanza <<< -->
