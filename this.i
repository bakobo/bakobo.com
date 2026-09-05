# bakobo.com — Intent Tree (this.i)
#
# Source of truth for this repo's intentions and the decisions that follow. The site (index.html,
# assets/, and the generated .well-known/ surface) is derived from it. Format: dhh1128/intent node
# tree; see bakobo/dev/methodology.md.
# Node key line:  Name = [marks...] type:   (types: goal | decision | constraint | tension | deviation)
# id: opaque base32 [a-z2-7]{8}, never a semantic label.  why: meets the rebuttal-surface standard.
#
# This repo ran without intent from its first commit until 2026-09-04, on the methodology §2 exemption
# for pure content repos, and that was the right call for a one-page placeholder. Publishing a KERI
# discovery endpoint ends the exemption: a discovery endpoint is an external contract and a trust
# claim, which is exactly the class of thing §3 says cannot be decided implicitly. The tree therefore
# starts here rather than being back-filled from the placeholder's history.

Serve bakobo.com — a deliberately quiet page for humans, a load-bearing directory for machines = goal:
  id: 7vpcnhmt
  why: >
    One repository owns everything published at the apex, which is now two audiences with opposite
    needs: a placeholder that reveals nothing about what Bakobo is building, and a machine-readable
    directory that tells a stranger precisely which AIDs and endpoints are Bakobo's. Rejected splitting
    them across two repos or two hostnames — the discovery endpoint's whole value is that it is at the
    apex, where a stranger who knows only the company name will look, and a second repo publishing to
    the same origin would mean two deploys racing for one Pages artifact. Accepted tradeoff: a public
    repo now carries both the strictest confidentiality rule in the org (@feshtwgl) and its most
    externally-consequential published claim (@lbk6u4ru), so every change here is reviewed against both.

  children:

    Stealth covers product strategy, not the technology stack = decision:
      id: feshtwgl
      why: >
        Decided 2026-09-04. The placeholder exists so competitors cannot read Bakobo's product plans off
        the front page, and tests/test_site.py::test_no_stealth_leak enforces it by banning "sedi",
        "keri", "acdc", "utah" and "reissuer" from the published copy. That test was written as though
        the secret were the technology; it is not. What Bakobo is building for whom is confidential;
        that Bakobo runs KERI infrastructure is not, and pretending otherwise buys nothing while costing
        the discovery endpoint entirely. Rejected two alternatives that would have preserved the broader
        reading: waiting until stealth lifts, which defers indefinitely a thing with value now, and
        publishing under wit.bakobo.com, which hides the endpoint from the one place a stranger looks
        while revealing the same facts to anyone who resolves the name. Accepted tradeoff, and it is a
        one-way door: a .well-known path that has been live is archived, mirrored and indexed, so this
        cannot be walked back by deleting files. The stealth test keeps its scope — index.html and the
        social card, the surfaces that speak about the business — and the generated .well-known/ tree is
        deliberately outside it, because there the terms are the payload.

    Adopt GLEIF's published .well-known contract as it stands, rather than improving on it = decision:
      id: sv6rtl3k
      stage-status: planned
      why: >
        The reason to adopt is to understand GLEIF's endpoint and ours the same way, which a surface
        that differs defeats. So the published files copy their current contract exactly — an RFC 6415
        host-meta.json, a flat type-agnostic /.well-known/oobi/{said}/index.json, a generated catalog at
        /.well-known/oobi/index.json, and the recommended human .well-known/index.html — including two
        choices this repo thinks are wrong: origin-scoped rel URIs, which make a generic cross-publisher
        client impossible, and a catalog that no longer carries the $id SAID earlier generations had, so
        the directory is unauthenticated. Rejected implementing from the two PRs the GLEIF announcement
        cited: both are superseded, GLEIF deleted the STRUCTURE.md and SCHEMA.md that read as a
        specification along with the layout they described, and there is no successor spec — the live
        surface and their build script are the only authority. See docs/gleif-well-known.md in
        bakobo/infra, which is private because it names the witness AIDs. Accepted tradeoff: the
        convention has changed shape three times in ten months, so this is a moving target and the
        generator must stay cheap to re-point. Improvements are deferred to @uymk2j6q rather than
        folded in here, so that what we publish stays a faithful reading of theirs.

    Nothing in the published surface is hand-typed = decision:
      id: mwa7fvu6
      stage-status: planned
      why: >
        A stale entry in a discovery document is worse than no document, because it is confidently
        wrong: it names an endpoint a stranger will believe is ours after it has stopped being ours.
        The estate is therefore the source, in two parts that fall out of where the facts actually
        live. `tofu output -json witnesses` in bakobo/infra owns the HOSTNAME LIST and nothing else —
        it has no AIDs, because those are minted on the host at inception and never enter tofu state.
        Each witness owns its own IDENTITY: fetching https://<host>/oobi yields a signed inception
        event whose AID must equal the sole key in `k`, which a non-transferable identifier lets the
        generator verify without trusting the fetch or the TLS. Published bodies are byte-exact copies
        of that CESR stream — re-serialising JSON would reorder keys and invalidate the attached
        signature, which is why GLEIF's own script copies bytes rather than parsing and re-emitting.
        Rejected a hand-maintained list committed here, which is the second-copy-that-can-be-wrong that
        ansible/bin/gen-inventory exists in infra to avoid.

    The generator lives in infra; two guards watch the boundary it crosses = decision:
      id: klykqkst
      stage-status: planned
      why: >
        Generation needs tofu state, which means AWS credentials and a private repo; the output belongs
        in a public one. Chose to put the generator in bakobo/infra beside the tofu root it reads, have
        it write into a bakobo.com checkout, and land the result as an ordinary reviewed PR here.
        Rejected generating in bakobo.com's CI, which would require estate credentials in a public
        repo's workflow. Rejected committing a witness-list export from infra into this repo, which
        reintroduces the second copy @mwa7fvu6 rules out, merely generated rather than typed. Because
        the output is committed rather than built on demand, two guards replace the freshness that a
        live build would have given: this repo's CI re-fetches each published OOBI and fails if the
        committed bytes no longer match what the witness serves, which needs no credentials; and a
        scheduled check in infra compares tofu's hostname set against the published catalog, which is
        the only place a REMOVED witness can be detected, since this repo cannot know about a host that
        is no longer in the estate. Accepted tradeoff: the endpoint is as fresh as the last PR, so a
        witness rotation is visible within a scheduled-check interval rather than immediately.

    The endpoint claims availability, and says so rather than letting a reader assume more = decision:
      id: lbk6u4ru
      stage-status: planned
      why: >
        infra's @2k5gid commits Bakobo to stating plainly, in published trust documentation, that the
        pool provides availability and not controller-accountability, because Bakobo operates both the
        AIDs and every witness (@nqaufp) — so a validator relying on these receipts learns that the
        events were served, not that an independent party vouched for them. A catalog that lists four
        witnesses under Bakobo's own name with no such note lets a reader supply the stronger reading
        for free, and a discovery endpoint is exactly where that reading gets made. The qualification
        goes in the human .well-known/index.html, which GLEIF's convention already recommends, and in
        the catalog's `description` so a machine client carries it too. Rejected putting it on the site's
        index.html, which is the placeholder and speaks to a different audience. Wording is approved by
        Daniel before publication rather than drafted and shipped, because it is a claim about what
        Bakobo's infrastructure is worth to a stranger.

    Schemas are not re-served here; the apex publishes only what it owns = decision:
      id: 7ufzxzip
      stage-status: planned
      why: >
        bakobo/schema already publishes a live registry at schema.bakobo.com — 17 ACDC schemas, each a
        byte-exact OOBI at /oobi/{said}.json, a discovery manifest at /.well-known/acdc-schemas.json, and
        a JSON Schema describing that manifest — under its own intent (@pv6k3d, @f7dr3k in that repo).
        Copying those OOBIs into this repo's flat mirror would put seventeen signed artifacts at a second
        origin with a second update path, which is the failure @mwa7fvu6 rejects, and would make the two
        surfaces disagree the first time a schema is re-minted. So the apex catalog carries witnesses now
        and organisational AIDs when they exist, and schemas stay where they are. Accepted tradeoff, and
        it is the sharpest gap in GLEIF's model: their flat namespace has no way to express "this class of
        resource is published at another origin, on our authority", so until @uymk2j6q there is no
        machine-readable pointer from the apex to schema.bakobo.com, only prose in the human page.

    No external-references section, and no pointer at GLEIF = decision:
      id: v7rjsabf
      stage-status: planned
      why: >
        Message 44 advertised a placeholder structure for linking to other participants' .well-known
        endpoints, and WebOfTrust's PR shipped one containing a single example.org entry. GLEIF then
        dropped it: it is absent from the live surface, and their generator emits a footer link only if
        an external/ directory happens to exist. Chose to omit ours rather than publish a section whose
        only plausible entry points at an organisation Bakobo has no announced relationship with —
        linking outward from a trust surface asserts something, and there is nothing here to assert. This
        is a why-not recorded so the next person does not read the announcement, notice the gap, and
        helpfully fill it in.

    Improvements on GLEIF's mechanism ship separately, or not at all = decision:
      id: uymk2j6q
      stage-status: planned
      why: >
        Deferred 2026-09-04, and recorded because deferring is itself the decision. Four gaps are worth
        addressing and none of them justify diverging from @sv6rtl3k inside the files GLEIF defines: the
        catalog is unsigned and un-SAID'd, which from an organisation whose technology is self-certifying
        identifiers is the conspicuous one, since a compromised deploy rewrites which AIDs a stranger
        trusts and nothing detects it; `updated` is a bare date with no expiry, so a cached copy never
        goes stale on purpose; there is no cross-origin delegation, which Bakobo needs today (@7ufzxzip);
        and a withdrawn witness simply vanishes, so a client holding a cached entry cannot distinguish
        retired from unreachable. If these are built they go in a sibling file — host-meta-v2.json — that
        a consumer can ignore, so the GLEIF-conformant surface stays exactly conformant. Rejected
        proposing them upstream first, which blocks our own endpoint on someone else's review cycle;
        bakobo/schema's @f7dr3k already positions Bakobo as a reference for discovery patterns, so
        publishing a working v2 and then proposing it is the stronger order.
      children:

        Delegation is a hint, and says so in the document = decision:
          id: bio6glms
          stage-status: planned
          why: >
            The first piece of @uymk2j6q to be built, and the choice is what "on our authority"
            means to a consumer rather than what the JSON looks like. Two readings were on the
            table. A HINT is a machine-readable pointer that saves a round trip and conveys no
            trust: the consumer still evaluates schema.bakobo.com on its own terms, exactly as it
            would have without us. An ENDORSEMENT is the apex vouching for the other origin, so
            that trusting bakobo.com extends to trusting what it names. Chose the hint, and made
            the choice explicit in the document as `"strength": "hint"` rather than leaving a
            reader to infer it, because a delegation with no stated strength will be read as the
            stronger one by anyone predisposed to.
            The endorsement is not merely deferred for effort: it would be dishonest to publish
            today. An endorsement is only worth what its signature is worth, and Bakobo has
            incepted no organisational AID to sign with (@7vpcnhmt) -- so an unsigned assertion
            that one origin vouches for another is a claim a network attacker can forge by
            replacing the file, which is the same unauthenticated-directory problem @uymk2j6q
            already names as GLEIF's conspicuous gap. Shipping the weak form now costs nothing and
            forecloses nothing; the strong form waits for a key. Accepted tradeoff: consumers get
            less than they might want from the apex, and @7ufzxzip's prose remains the only place
            the relationship is asserted rather than merely indicated.
