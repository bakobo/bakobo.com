# bakobo.com

[![Pages](https://github.com/bakobo/bakobo.com/actions/workflows/pages.yml/badge.svg)](https://github.com/bakobo/bakobo.com/actions/workflows/pages.yml)

The corporate website for **Bakobo LLC** — currently a stealth-mode placeholder.
One page: the brand, the rallying cry (*Act. Don't be acted upon.*), and a way
to reach us. No product details, by design.

It's a hand-authored static site (no site generator) styled from the Bakobo
brand kit, deployed to GitHub Pages at **https://bakobo.com/**.

## Layout

| Path | Contents |
|------|----------|
| `index.html` | the whole site — hero, stance, footer, plus canonical/OG/JSON-LD |
| `assets/css/tokens.css` | brand palette & type as `--bk-*` custom properties — **vendored, generated** (source of truth is the sibling `../brand` repo; do not hand-edit) |
| `assets/css/site.css` | the design layer (warm dark hero, grain, staggered reveal) |
| `assets/img/` | logo, trustmark, favicons, and the generated `og-card.png` — vendored from `../brand` |
| `assets/social/card.html` | reproducible generator for the 1200×630 social card |
| `robots.txt`, `sitemap.xml` | pure-signal SEO |
| `CNAME`, `.nojekyll` | Pages custom domain + verbatim asset serving |
| `tests/` | stdlib + pytest checks (assets resolve, SEO/JSON-LD valid, card is 1200×630, no stealth leaks) |

## Fresh clone → passing tests

Tests are Python (stdlib only) run under [pytest](https://pytest.org). With
[uv](https://docs.astral.sh/uv/):

```bash
uv run --with pytest pytest
```

Or with a plain virtualenv:

```bash
python -m pip install pytest
pytest
```

## Preview locally

```bash
python -m http.server 8199
# open http://localhost:8199/
```

## Regenerate the social card

Edit `assets/social/card.html`, then render it at exactly 1200×630 (any headless
Chromium works) while the preview server is running:

```bash
chromium --headless --window-size=1200,630 --virtual-time-budget=2500 \
  --screenshot=assets/img/og-card.png \
  http://localhost:8199/assets/social/card.html
```

## Deploy

Pushing to `main` runs the tests and, if green, deploys to GitHub Pages via
`.github/workflows/pages.yml`. The repo's **Settings → Pages → Source** must be
set to **GitHub Actions** (one-time), and the `bakobo.com` DNS must point at
GitHub Pages.

## Brand

Brand assets and rationale live in the sibling `../brand` repo (start with
`docs/essence.md`). When the brand kit changes, re-vendor the affected files
here (`tokens.css`, logos, favicons) rather than editing them in place.
