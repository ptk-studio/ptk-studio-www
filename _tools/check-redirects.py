#!/usr/bin/env python3
"""Every URL that must keep working after the move to mochi-factory.com (ptk-studio-www#33 step 2).

For each path (all pages in this repo + every <loc> in sitemap.xml), checks:
  https://ptk-studio.com<path>  ->  301 (or 308)  ->  Location https://mochi-factory.com<path>  ->  200
Read-only (HEAD/GET). Exit 1 if any URL fails. Usage: python3 _tools/check-redirects.py [--old HOST] [--new HOST]
"""
import argparse, re, sys, urllib.request, urllib.error
from pathlib import Path
R = Path(__file__).resolve().parents[1]
ap = argparse.ArgumentParser(); ap.add_argument('--old', default='ptk-studio.com'); ap.add_argument('--new', default='mochi-factory.com')
a = ap.parse_args()
paths = {'/'}
for p in R.rglob('index.html'):
    rel = p.relative_to(R).parent.as_posix()
    if rel.startswith(('_tools', '.git')): continue
    paths.add('/' if rel == '.' else f'/{rel}/')
for loc in re.findall(r'<loc>https?://[^/]+(/[^<]*)</loc>', (R / 'sitemap.xml').read_text()):
    paths.add(loc)
for extra in ('/sitemap.xml', '/robots.txt', '/blog/feed.xml'):
    paths.add(extra)

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kw): return None
opener = urllib.request.build_opener(NoRedirect)
UA = {'User-Agent': 'Mozilla/5.0 (redirect check)'}

def status(url, follow=False):
    req = urllib.request.Request(url, headers=UA, method='GET')
    try:
        r = (urllib.request.urlopen if follow else opener.open)(req, timeout=20)
        return r.status, r.headers.get('Location', '')
    except urllib.error.HTTPError as e:
        return e.code, e.headers.get('Location', '')
    except Exception as e:
        return 0, str(e)[:60]

fails, rows = 0, []
for path in sorted(paths):
    old, new = f'https://{a.old}{path}', f'https://{a.new}{path}'
    s1, loc = status(old)
    s2, _ = status(new, follow=True)
    ok = s1 in (301, 308) and loc.rstrip('/') == new.rstrip('/') and s2 == 200
    fails += not ok
    rows.append(f"| {'OK' if ok else 'FAIL'} | `{path}` | {s1} → {loc or '-'} | {s2} |")
print(f'| | Path | {a.old} | {a.new} |\n|---|---|---|---|\n' + '\n'.join(rows))
print(f'\n{len(rows)} URLs, {fails} failing.')
sys.exit(1 if fails else 0)
