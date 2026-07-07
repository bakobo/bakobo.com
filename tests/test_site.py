"""Static-site checks for bakobo.com.

Stdlib only (no third-party deps beyond pytest itself). These guard the things
that quietly break a placeholder: a moved asset, malformed JSON-LD, a stale
canonical, a social card that isn't 1200x630, a robots.txt that stops being a
pure signal.
"""

from __future__ import annotations

import json
import re
import struct
from html.parser import HTMLParser
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://bakobo.com"


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


class _Collector(HTMLParser):
    """Collect (tag, {attrs}) for every start/startend tag."""

    def __init__(self) -> None:
        super().__init__()
        self.tags: list[tuple[str, dict[str, str]]] = []

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, {k: (v or "") for k, v in attrs}))

    handle_startendtag = handle_starttag


def _parse(html: str) -> _Collector:
    c = _Collector()
    c.feed(html)
    return c


# --- structural -----------------------------------------------------------

def test_index_exists_and_parses():
    tags = _parse(read("index.html")).tags
    assert any(t == "h1" for t, _ in tags), "expected an <h1>"


def test_lang_and_charset():
    html = read("index.html")
    assert re.search(r'<html[^>]*\blang="en"', html)
    assert re.search(r'<meta[^>]*\bcharset="utf-8"', html, re.I)


# --- SEO / social ---------------------------------------------------------

def _meta(html: str, *, name=None, prop=None) -> str | None:
    for tag, attrs in _parse(html).tags:
        if tag != "meta":
            continue
        if name and attrs.get("name") == name:
            return attrs.get("content")
        if prop and attrs.get("property") == prop:
            return attrs.get("content")
    return None


def test_canonical_is_apex_https():
    html = read("index.html")
    hrefs = [a.get("href") for t, a in _parse(html).tags
             if t == "link" and a.get("rel") == "canonical"]
    assert hrefs == [f"{SITE}/"], hrefs


def test_required_meta_present():
    html = read("index.html")
    assert _meta(html, name="description")
    assert _meta(html, prop="og:title")
    assert _meta(html, prop="og:description")
    assert _meta(html, prop="og:url") == f"{SITE}/"
    assert _meta(html, prop="og:image") == f"{SITE}/assets/img/og-card.png"
    assert _meta(html, name="twitter:card") == "summary_large_image"


def test_no_stealth_leak():
    """The placeholder must not reveal strategy. Guard the obvious terms."""
    haystack = " ".join(
        read(p).lower() for p in ("index.html", "assets/social/card.html")
    )
    for banned in ("sedi", "keri", "acdc", "utah", "reissuer"):
        assert banned not in haystack, f"stealth leak: {banned!r} appears in site copy"


def test_jsonld_is_valid_organization():
    html = read("index.html")
    m = re.search(
        r'<script type="application/ld\+json">(.*?)</script>', html, re.S
    )
    assert m, "no JSON-LD block"
    data = json.loads(m.group(1))  # raises if malformed
    assert data["@type"] == "Organization"
    assert data["legalName"] == "Bakobo LLC"
    assert data["url"] == f"{SITE}/"
    assert data["email"] == "info@bakobo.com"


# --- assets resolve -------------------------------------------------------

def _local_refs(html: str) -> set[str]:
    refs: set[str] = set()
    for _tag, attrs in _parse(html).tags:
        for key in ("href", "src"):
            v = attrs.get(key, "").split("?", 1)[0].split("#", 1)[0]
            # root-relative file refs only; skip page links ("/", "/foo/")
            if v.startswith("/") and not v.startswith("//") and not v.endswith("/"):
                refs.add(v)
    return refs


def test_all_root_relative_assets_exist():
    for ref in _local_refs(read("index.html")):
        target = ROOT / ref.lstrip("/")
        assert target.is_file(), f"missing asset referenced in index.html: {ref}"


def test_favicon_at_web_root():
    # browsers request /favicon.ico regardless of <link> tags
    assert (ROOT / "favicon.ico").is_file()


# --- social card ----------------------------------------------------------

def _png_size(path: Path) -> tuple[int, int]:
    with path.open("rb") as fh:
        head = fh.read(24)
    assert head[:8] == b"\x89PNG\r\n\x1a\n", "not a PNG"
    w, h = struct.unpack(">II", head[16:24])
    return w, h


def test_og_card_is_1200x630():
    assert _png_size(ROOT / "assets/img/og-card.png") == (1200, 630)


# --- robots & sitemap -----------------------------------------------------

def test_robots_is_pure_signal():
    robots = read("robots.txt")
    assert "Sitemap: https://bakobo.com/sitemap.xml" in robots
    assert "Disallow: /.well-known/" in robots


def test_sitemap_wellformed_and_lists_home():
    root = ET.fromstring(read("sitemap.xml"))
    ns = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
    locs = [e.text for e in root.iter(f"{ns}loc")]
    assert locs == [f"{SITE}/"], locs


def test_cname_matches_apex():
    assert read("CNAME").strip() == "bakobo.com"
