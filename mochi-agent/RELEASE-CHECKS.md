# RELEASE-CHECKS: Mochi Factory site (mochi-factory.com)

Run before any release (deploy, publish or upload).

## First visit (blocking; ptk-studio#235, #237)

**Before any release: run every check in this file; the First visit section is blocking.** Nothing is deployed or
published until every row passes with its evidence on the scorecard. Open the site **as a stranger**: a fresh browser
profile, no cookies, a phone-size window.

| # | Check | Passes when (evidence) |
|---|---|---|
| FV1 | Every public page in the sitemap | HTTP 200, the right title, renders at phone width (a screenshot per changed page) |
| FV2 | Console | **0 errors** on every changed page (the console log) |
| FV3 | Network | only the hosts the privacy page names; our APIs only via `api.88eggs.com` (R53); no response ≥ 400 |
| FV4 | Cookies | before consent: none beyond what the privacy page lists; after consent: exactly the listed ones |
| FV5 | Forms and the Feedback button | open and validate; **never submit against production** (a test submit only on local or staging) |
| FV6 | Redirects and old URLs | every URL that must keep working answers (e.g. `_tools/check-redirects.py` where it exists) |
| FV7 | The scorecard line | `First visit on a fresh profile: PASS (evidence)` |
