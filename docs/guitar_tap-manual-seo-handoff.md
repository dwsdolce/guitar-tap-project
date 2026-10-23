# Guitar Tap — Manual URL / SEO Handoff

Context brief for continuing in a session that has all five repos:
the three ports (**GuitarTap** Swift, **guitar_tap** Python, **GuitarTapWeb** web),
the **marketing website** repo, and the **central PM** repo.

Prepared from a session that had read access only to the website repo and
`GuitarTap/Documentation/Manual/`. **No changes were made to any repo.**

## Decisions and what is done (owner, 2026-10-23)

1. **Canonical target: Option B** — `/guitar_tap/manual/` is a real page, and every copy of the manual names it
   as canonical.
2. **Generator** (`generate-manual.sh`): the manual's `<head>` carries
   `<link rel="canonical" href="https://www.dolcesfogato.com/guitar_tap/manual/">`, and `index.html` is a copy of
   the manual instead of the redirect stub.
3. **Already-deployed versions edited directly**, not regenerated (the manual sources now hold 1.0.3 material):
   the canonical line added to `GuitarTap-User-Manual-1.0.html`, `-1.0.1.html`, `-1.0.2.html` and the unversioned
   copy; `manual/index.html` is the 1.0.2 manual. No `.htaccess`.
4. **Website:** the homepage links `manual/`, not `manual/index.html`.
5. All three editions link only the version-numbered file (Swift `DocumentationLinks.swift`, Python
   `_open_user_manual`, web `App.tsx`) — checked.

**Still to do:** the owner's cPanel upload of the five manual files and the homepage; check the live files carry
the canonical and `/manual/` is the manual; request re-indexing in Search Console and watch the report clear;
then #15 closed.

---

## The trigger

Google Search Console reports `https://www.dolcesfogato.com/guitar_tap/manual/`
as **"Page is not indexed: Page with redirect."** It is discovered via the
sitemap, and Google selected `.../manual/GuitarTap-User-Manual-1.0.1.html` as the
canonical (a *versioned* filename, and already stale — the site now redirects to
1.0.2).

This is one of a class of manual‑related GSC reports that will recur every
release unless the underlying pattern changes.

## Root cause

`/guitar_tap/manual/` is served by `manual/index.html`, which is **not** the
manual — it is a redirect stub (all three at once):

```html
<meta http-equiv="refresh" content="0; url=GuitarTap-User-Manual-1.0.2.html">
<link rel="canonical" href="GuitarTap-User-Manual-1.0.2.html">
<script>location.replace("GuitarTap-User-Manual-1.0.2.html");</script>
```

So the sitemap URL genuinely redirects → "Page with redirect" is *accurate*, not a
bug. Two compounding issues:

1. The stub redirects to a **version‑numbered** file, so the URL Google indexes
   moves every release, and the previous version is left behind as a live 200 page.
2. The full manual HTML files (`GuitarTap-User-Manual-X.Y.html`, plus the
   `GuitarTap-User-Manual.html` latest‑copy) carry **no canonical tag**, so the
   several near‑identical copies compete as duplicates ("Duplicate without
   user‑selected canonical" territory).

## How the files are produced

`GuitarTap/Documentation/Manual/generate-manual.sh` (runs in the **Swift** repo;
reads `MARKETING_VERSION` from `GuitarTap.xcodeproj/project.pbxproj`) emits into
`Documentation/Manual/`, which is then copied into the website repo's `manual/`
each release (manual cPanel upload; static site, no build step). Outputs:

- `GuitarTap-User-Manual-${VERSION}.html` / `.pdf`  — the real manual (assembled)
- `GuitarTap-User-Manual.html` / `.pdf`             — stable "latest" copies (`cp`)
- `index.html`                                      — the redirect stub (the problem)

Note: the **deployed** HTML is ~7 MB because images are embedded (self‑contained);
the freshly generated source HTML is ~209 KB with external images. Expected — just
confirm the live manual is current on redeploy.

## Constraints established (do not break these)

- **Versioned files must keep existing.** All three ports (Swift / Python / Web)
  deep‑link the *versioned* manual file (e.g. `GuitarTap-User-Manual-1.0.2.html`),
  not the `/manual/` directory. Any solution must keep the versioned files present
  and reachable.
- **App Store does not reference the manual.** Its only link is to the
  `/guitar_tap` landing page. So no App Store dependency on `/manual/`.
- **`support.html` advertises a clean, typable URL** to users as visible text:
  `dolcesfogato.com/guitar_tap/manual`. This is the main remaining reason to keep
  `/manual/` resolving (as a real page) rather than deleting it.
- Host is **cPanel / Apache** → `.htaccess`, `mod_headers`, `mod_rewrite` available.

## Every internal reference to the manual (website repo)

| File / line | Current | Notes |
|---|---|---|
| `index.html:290` | `<a href="manual/index.html">` | homepage "User Manual — online" → the stub |
| `index.html:291` | `<a href="manual/GuitarTap-User-Manual.pdf">` | PDF, already a direct stable file (leave) |
| `releases/index.html:55` | `<a href="../manual/">` | links the bare directory |
| `support.html:65` | `<a href="manual/">dolcesfogato.com/guitar_tap/manual</a>` | bare dir **and** advertised URL text |
| `sitemap.xml:16` | `<loc>…/guitar_tap/manual/</loc>` | sitemap entry (PDF entry already stable) |

Ports (Swift/Python/Web) and App Store description body were **not** grep‑verified
in this session — confirm they only use versioned filenames.

---

## Candidate solutions (both eliminate the redirect)

### Option B — keep `/manual/` as a real page  *(recommended)*

Rationale: preserves the advertised `…/guitar_tap/manual` URL, fewest site edits,
and consolidates every version/copy onto one stable URL.

Generator changes in `generate-manual.sh`:

1. Add a self‑canonical to the assembled `<head>` (applies to versioned + latest
   copy + index):

   ```diff
      <title>GuitarTap User Manual</title>
   +  <link rel="canonical" href="https://www.dolcesfogato.com/guitar_tap/manual/">
      {style_block}
   ```

2. Replace the "Generating redirect index.html" block so `/manual/` serves the
   manual directly instead of redirecting:

   ```diff
   - # ...writes the meta-refresh/JS redirect stub to index.html...
   - cat > "$INDEX_OUT" <<HTMLEOF ... HTMLEOF
   + INDEX_OUT="$OUTPUT_DIR/index.html"
   + cp "$FULL_HTML" "$INDEX_OUT"
   ```

Result: `/guitar_tap/manual/` is a normal 200 page canonical to itself; the
version‑numbered files the apps link still work but declare `/manual/` canonical,
so they consolidate instead of competing. Sitemap already points at `/manual/`.
Site links can stay as‑is (optionally simplify `manual/index.html` → `manual/`).

### Option A — retire `/manual/`, reference the file directly (like the PDF)

Delete the `index.html` stub from the generator. Reference the stable‑named
`GuitarTap-User-Manual.html` everywhere, exactly as the PDF is referenced. Give it
a self‑canonical to its own file URL; versioned files canonical to that file URL.

Edits: repoint `index.html:290`, `releases/index.html:55`, `support.html:65` to
`manual/GuitarTap-User-Manual.html`; change `sitemap.xml:16` to the file URL.
Downside: the advertised `…/guitar_tap/manual` URL 403s if typed (bare directory,
no index) — would need to update the `support.html` displayed text.

### Alternative mechanism (either option) — server‑side via `manual/.htaccess`

Fixes indexing without touching the generator, and can retroactively canonicalize
**already‑deployed old versioned files** (`1.0`, `1.0.1`) that predate any generator
change:

```apache
DirectoryIndex GuitarTap-User-Manual.html
<Files "GuitarTap-User-Manual.html">
  Header set Link "<https://www.dolcesfogato.com/guitar_tap/manual/>; rel=\"canonical\""
</Files>
<FilesMatch "^GuitarTap-User-Manual-[0-9._]+\.html$">
  Header set Link "<https://www.dolcesfogato.com/guitar_tap/manual/>; rel=\"canonical\""
</FilesMatch>
RewriteEngine On
RewriteRule ^index\.html$ https://www.dolcesfogato.com/guitar_tap/manual/ [R=301,L]
```

## Open decisions for the multi‑repo session

1. **Canonical target:** directory `/manual/` (Option B) vs file
   `…/GuitarTap-User-Manual.html` (Option A). The advertised support‑page URL
   favors B.
2. **Old deployed versions** (`1.0`, `1.0.1`): leave to age out (not in sitemap,
   only reached by old in‑app links) or mop up via the `.htaccess` `FilesMatch`.
3. **Generator vs server fix vs both:** generator = clean going forward but only
   affects newly built files; `.htaccess` = instant + retroactive but logic lives
   in server config.
4. **Confirm all three ports** link only versioned filenames (grep Swift/Python/Web
   help/menu code) before committing to canonical‑to‑stable.

---

## Appendix — other GSC items triaged in the same session

- **`/guitar_tap` (no trailing slash) — "Page with redirect":** expected/harmless
  (redirects to `/guitar_tap/`). Root cause was a homepage internal link missing
  the trailing slash; **already fixed** (homepage now links `…/guitar_tap/`). May
  linger in GSC; not an error.
- **`…/Music/Baroque_lute/La Rhétorique` — 404:** external referring page
  (`mail-archive.com` lute list) auto‑linked a URL and truncated it at a space
  (`La Rhétorique des Dieux.pdf` → `La Rhétorique`). Not a site problem; the real
  PDF is 200. Optional 301 from the truncated path if recovering that click matters.
- **`…/Music/Hortus Musicalis Novus [1615] Complete Nr. 3.pdf` — "Duplicate
  without user‑selected canonical":** identical PDF also hosted on
  `fandango.musickshandmade.com`; Google picked the other copy. Harmless. Only act
  (HTTP canonical header, or a unique HTML landing page) if you want your copy to
  win.

General rule the site owner is now using: reports driven by an **external
referring page** or **another site's duplicate** are Google narrating reality
(safe to close); only broken links / missing files / bad redirects on the site's
own server warrant real work.
