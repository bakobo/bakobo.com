#!/usr/bin/env python3
"""Prove the published .well-known surface still matches what the witnesses serve.

The discovery tree is generated in bakobo/infra and committed here (this.i @klykqkst), so between
generator runs it is a static file describing a live estate. This is the guard for that gap: fetch
each published witness at its own hostname and require the bytes to be identical to what we serve
from the apex. Byte-identical rather than semantically equal, because these are signed CESR streams
and a body that differs at all no longer carries a valid signature.

What this CANNOT see is a witness that left the estate, because a decommissioned host is absent from
the catalog this walks and so is never asked about. Only a check with tofu access can catch that;
it lives in infra (@llwkkf4y there). Do not let this script's passing be read as "the surface is
complete" -- it means "everything the surface claims is still true".

Needs network but no credentials. Exit 0 clean, 1 on any drift or unreachable witness.
"""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CATALOG = ROOT / ".well-known" / "oobi" / "index.json"
TIMEOUT = 20


def check() -> int:
    catalog = json.loads(CATALOG.read_text())
    entries = {
        aid: entry
        for group in catalog["resources"].values()
        for aid, entry in group.items()
    }
    if not entries:
        print("error: the published catalog is empty, which the generator refuses to produce.",
              file=sys.stderr)
        return 1

    failures = 0
    for aid in sorted(entries):
        entry = entries[aid]
        hostname = entry.get("hostname")
        if not hostname:
            print(f"FAIL {aid}: published without a hostname, so it cannot be re-checked here.",
                  file=sys.stderr)
            failures += 1
            continue

        url = f"https://{hostname}/oobi"
        try:
            with urllib.request.urlopen(url, timeout=TIMEOUT) as resp:
                live = resp.read()
        except (urllib.error.URLError, OSError) as exc:
            print(f"FAIL {entry.get('name', aid)} ({hostname}): {url} is unreachable: {exc}. "
                  "A restarting witness looks like this, so re-run before treating it as an outage.",
                  file=sys.stderr)
            failures += 1
            continue

        published = (ROOT / entry["oobi"].lstrip("/")).read_bytes()
        if live != published:
            print(f"FAIL {entry.get('name', aid)} ({hostname}): the witness now serves "
                  f"{len(live)} bytes that differ from the {len(published)} we publish. Either the "
                  "witness was rebuilt with a new identity or the committed file was edited; "
                  "regenerate from infra rather than patching this repo.", file=sys.stderr)
            failures += 1
            continue

        print(f"ok   {entry.get('name', aid):4} {hostname:22} {aid}")

    if failures:
        print(f"\n{failures} of {len(entries)} published OOBIs no longer match their witness.",
              file=sys.stderr)
        return 1
    print(f"\nall {len(entries)} published OOBIs are byte-identical to what their witness serves.")
    print("note: this cannot detect a witness removed from the estate -- see infra's scheduled check.")
    return 0


if __name__ == "__main__":
    raise SystemExit(check())
