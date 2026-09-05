# Deploying rickykhamis.com on Vercel

## What is committed here

Nothing that can be served yet. `site/` — the directory both `netlify.toml`
and `vercel.json` publish — is **generated**, not committed. It is produced by
`scripts/mirror_site.py`, which scrapes the live rickykhamis.com. That script
has never run: the repository has zero workflow runs and `site/` appears
nowhere in history.

**Deploying today would publish an empty directory.** Do not point a domain at
it until `site/` exists.

## Order of operations

1. **Generate the mirror.** Run the `Mirror live site` workflow
   (Actions -> Mirror live site -> Run workflow). It fetches the sitemap,
   downloads every page and asset, writes `site/`, and commits it back.
   It refuses to commit a mirror under 100 pages, so a truncated scrape
   cannot overwrite a good one.
2. **Recover the redirects.** The live Netlify deploy serves 72 redirect
   rules. Netlify consumes `_redirects` at deploy time and never serves it
   over HTTP, so the mirror cannot fetch it — `mirror_site.py` prints a
   warning when it is missing. Export the rules from the Netlify UI.
3. **Translate the redirects for Vercel.** Vercel does not read Netlify's
   `_redirects` format. Each rule becomes an entry in the `redirects` array
   in `vercel.json`:

   ```json
   "redirects": [
     { "source": "/old-path", "destination": "/new-path", "permanent": true }
   ]
   ```

   Skipping this silently 404s every one of those URLs.
4. **Create the Vercel project** against this repository. `vercel.json`
   already sets output directory `site` with no build or install step, so
   the dashboard needs no further configuration.
5. **Verify the preview deployment** before moving DNS. Spot-check the
   redirect rules and a page that loads fonts from inside CSS.

## Why no build step

The mirror is served byte-for-byte from the same origin it was copied from.
URLs are deliberately not rewritten, so absolute links keep resolving. There
is nothing to compile — Vercel just publishes the directory.
