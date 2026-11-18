#!/usr/bin/env python3
"""Rebuild the blog index list, blog/feed.xml and the site-wide sitemap.xml.

Run from the repo root after adding or changing a post:  python3 -I _tools/build-blog.py
A post is blog/<slug>/index.html made from _tools/blog-post.template; its title,
description and date are read from the <title>, meta description and
article:published_time tags. Posts are listed newest first.
"""
import html, os, re, subprocess, sys
from datetime import date
from email.utils import format_datetime
from datetime import datetime, timezone

SITE = "https://mochi-factory.com"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def meta(text, pattern):
    m = re.search(pattern, text, re.S)
    return html.unescape(m.group(1).strip()) if m else ""

def posts():
    out = []
    bdir = os.path.join(ROOT, "blog")
    for slug in sorted(os.listdir(bdir)):
        f = os.path.join(bdir, slug, "index.html")
        if not os.path.isfile(f):
            continue
        t = open(f, encoding="utf-8").read()
        title = re.sub(r"\s*·\s*Mochi Factory Blog$", "", meta(t, r"<title>(.*?)</title>"))
        d = meta(t, r'property="article:published_time" content="([^"]+)"')
        desc = meta(t, r'name="description" content="([^"]*)"')
        if not (title and d):
            sys.exit(f"blog/{slug}/index.html: missing <title> or article:published_time")
        out.append({"slug": slug, "title": title, "date": d, "desc": desc})
    return sorted(out, key=lambda p: p["date"], reverse=True)

def build_index(ps):
    f = os.path.join(ROOT, "blog", "index.html")
    t = open(f, encoding="utf-8").read()
    if ps:
        items = "\n".join(
            f'    <li><h2><a href="{p["slug"]}/">{html.escape(p["title"])}</a></h2>'
            f'<p class="post-meta"><time datetime="{p["date"]}">{p["date"]}</time></p>'
            f'<p>{html.escape(p["desc"])}</p></li>' for p in ps)
        body = f'  <ul class="post-list">\n{items}\n  </ul>'
    else:
        body = '  <p class="post-empty">The first posts are on their way.</p>'
    noindex = '<meta name="robots" content="noindex">\n'
    t = t.replace(noindex, "")
    if not ps:  # an empty blog stays out of search until the first post
        t = t.replace('<link rel="canonical"', noindex + '<link rel="canonical"', 1)
    new = re.sub(r"(<!-- POSTS:START[^>]*-->\n).*?(\n  <!-- POSTS:END -->)", lambda m: m.group(1) + body + m.group(2), t, flags=re.S)
    open(f, "w", encoding="utf-8").write(new)

def build_home_link(ps):
    f = os.path.join(ROOT, "index.html")
    t = open(f, encoding="utf-8").read()
    link = '<a href="/blog/">Blog</a>\n      <span class="dot">·</span>\n      ' if ps else ""
    new = re.sub(r"(<!-- BLOGLINK:START[^>]*-->).*?(<!-- BLOGLINK:END -->)", lambda m: m.group(1) + link + m.group(2), t, flags=re.S)
    open(f, "w", encoding="utf-8").write(new)

def rfc822(d):
    return format_datetime(datetime.fromisoformat(d).replace(tzinfo=timezone.utc))

def build_feed(ps):
    items = "".join(
        f"\n  <item><title>{html.escape(p['title'])}</title><link>{SITE}/blog/{p['slug']}/</link>"
        f"<guid>{SITE}/blog/{p['slug']}/</guid><pubDate>{rfc822(p['date'])}</pubDate>"
        f"<description>{html.escape(p['desc'])}</description></item>" for p in ps)
    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0">\n<channel>\n'
           f'  <title>Mochi Factory Blog</title>\n  <link>{SITE}/blog/</link>\n'
           '  <description>Short, practical posts from Mochi Factory.</description>\n  <language>en-us</language>'
           f'{items}\n</channel>\n</rss>\n')
    open(os.path.join(ROOT, "blog", "feed.xml"), "w", encoding="utf-8").write(xml)

def build_sitemap(ps):
    files = subprocess.run(["git", "-C", ROOT, "ls-files", "*.html"], capture_output=True, text=True, check=True).stdout.split()
    files += [f"blog/{p['slug']}/index.html" for p in ps]
    def indexable(f):
        p = os.path.join(ROOT, f)
        return not (os.path.isfile(p) and re.search(r'name="robots" content="[^"]*noindex', open(p, encoding="utf-8").read()))
    urls = sorted({f"{SITE}/" + f[: -len("index.html")] for f in files if f.endswith("index.html") and indexable(f)})
    dates = {f"{SITE}/blog/{p['slug']}/": p["date"] for p in ps}
    body = "".join(f"\n  <url><loc>{u}</loc>" + (f"<lastmod>{dates[u]}</lastmod>" if u in dates else "") + "</url>" for u in urls)
    xml = f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{body}\n</urlset>\n'
    open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8").write(xml)

if __name__ == "__main__":
    ps = posts()
    build_index(ps); build_home_link(ps); build_feed(ps); build_sitemap(ps)
    print(f"{len(ps)} posts; blog/index.html, blog/feed.xml and sitemap.xml rebuilt")
