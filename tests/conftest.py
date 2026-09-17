"""Shared test constants.

`BANNED` lives here because three suites enforce the same ban over three different scopes, and
until 2026-09-17 each carried its own copy of the list. Copilot caught that on PR #13: editing the
ban in one place left the others silently checking a policy the repository no longer holds, which is
the opposite of what the duplication was defended as buying.

The scopes are genuinely different and stay separate -- that part was right:

- `test_site.py::test_no_stealth_leak` and `test_wellknown.py::test_the_placeholder_still_says_nothing_about_the_stack`
  guard `index.html` and the social card, the two surfaces @feshtwgl scopes stealth to.
- `test_publish_set.py::test_no_staged_text_file_breaks_stealth` guards every text file the stager
  actually produces, with `.well-known/` exempt because there the terms are the payload.

One ban, three scopes. Not three bans.
"""

from __future__ import annotations

# The five terms @feshtwgl bans from anything that speaks about the business.
BANNED: tuple[str, ...] = ("sedi", "keri", "acdc", "utah", "reissuer")
