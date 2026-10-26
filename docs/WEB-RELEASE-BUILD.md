# The web edition's GitHub release carries its build

**Issue:** [#46](https://github.com/dwsdolce/guitar-tap-project/issues/46)

Status: **OPEN — plan agreed; nothing built.**

## The problem

Lutherie Academy will host GuitarTapWeb on their own site, as they host their other tools: a copy on their server.
They need the built app (`dist/`) for each release. Today there is no such file anywhere, and the web edition's GitHub
releases are out of date:

- **One release, 1.0.1**, with release notes and no files.
- **1.0.2 shipped** (tag `1.0.2`, build 213, deployed to dolcesfogato.com) but has **no GitHub release**.
- **No release workflow.** The repo's workflows are `test.yml` (tests) and `mint-baseline.yml`; the build is made by
  hand (`npm run build`) and uploaded to dolcesfogato.com through cPanel (release checklist §3).

## What a release would carry

`dist/` is the whole app: static files (about 1.6 MB), no server code, running from any folder (Vite `base: './'`)
over HTTPS, its Help linking to the manual on dolcesfogato.com. Zipped and attached to the release as
`guitar-tap-web-<version>.<build>.zip`, it is what Lutherie Academy installs and what we upload to dolcesfogato.com —
the same file from the same tag.

## Proposal

A workflow in GuitarTapWeb, `release.yml`, as Python's Linux AppImage workflow (`release-linux.yml`):

- **Runs when a release is published**, building its tag; **or by hand** for a tag, attaching the zip to that tag's
  release only when asked, otherwise keeping it as the run's artifact.
- **Checks out the tag with its whole history** — the build number is the commit count — and runs `npm ci` and
  `npm run build` (which type-checks first). At the tag itself the release guard passes, so a past release builds.
- **Node:** the tag's `.nvmrc` when it has one; otherwise `main`'s (`v26.11.1`). (The `1.0.2` tag has none.)
- **Checks the build:** the version and build number the app reports equal the tag's version and
  `git rev-list --count <tag>`.
- **Attaches** `guitar-tap-web-<version>.<build>.zip`.

GitHub runs a published release's workflow from the tagged commit, and the `1.0.2` tag has no workflow: 1.0.2 is
built by hand from `main`. A release tagged after the workflow exists builds itself when it is published.

## Decisions (owner, 2026-10-26)

1. **The GitHub release's notes are a short, marketing summary** — the release's enhancements, not the full notes
   the app shows (`ReleaseNotes.tsx`), which are far too long for it. Written for each release; how much of a draft
   can be taken from `ReleaseNotes.tsx` (its New Features and Improvements headings) is looked at when 1.0.2's are
   written.
2. **1.0.1 is left as it is** (notes, no build).
3. **1.0.2's build must match what is live.** The server is not thought to have had an untagged update; the check
   in step 3 confirms it. A mismatch is a failure to find before the zip is attached.

## Plan

1. `release.yml` in GuitarTapWeb, as above.
2. Run the workflow by hand for `1.0.2`, keeping the zip as the run's artifact.
3. Check that zip: it reports 1.0.2 (213); it runs from a plain folder (`python3 -m http.server`); its files match what
   is live at dolcesfogato.com/guitar_tap/guitar_tap_web/. Only then: the 1.0.2 GitHub release, with its marketing
   notes (the owner reviews them), and the zip attached.
4. The release checklist §3: the GitHub release is published with notes and the workflow attaches the build; the
   cPanel upload is that zip.
5. 1.1.0 is released this way.
