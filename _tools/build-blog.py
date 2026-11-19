#!/usr/bin/env python3
"""Rebuild the blog index list, blog/feed.xml and the site-wide sitemap.xml.

Run from the repo root after adding or changing a post:  python3 -I _tools/build-blog.py
A post is blog/<slug>/index.html made from _tools/blog-post.template; its title,
description, date and tags are read from the <title>, meta description,
article:published_time and article:tag tags. Posts are listed newest first. Tags come
from the small fixed set TAGS below; each gets a page at blog/tag/<tag>/, a link on
every post, the index and the feed (<category>).
"""
import html, os, re, subprocess, sys
from datetime import date
from email.utils import format_datetime
from datetime import datetime, timezone

SITE = "https://mochi-factory.com"
# The tag set stays small and consistent (the Owner, ptk-studio#259): a post may only use these, in this order.
TAGS = ["AI models", "blind tests", "AI images", "AI voice", "YouTube", "cost", "printables", "how-to"]
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def slugify(tag):
    return re.sub(r"[^a-z0-9]+", "-", tag.lower()).strip("-")

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
        tags = [html.unescape(x) for x in re.findall(r'<meta property="article:tag" content="([^"]+)"', t)]
        if not tags or any(x not in TAGS for x in tags):
            sys.exit(f"blog/{slug}/index.html: needs 1+ article:tag meta tags, each one of {TAGS}")
        out.append({"slug": slug, "title": title, "date": d, "desc": desc, "tags": sorted(set(tags), key=TAGS.index)})
    return sorted(out, key=lambda p: p["date"], reverse=True)

def tag_links(tags, prefix):
    return ", ".join(f'<a href="{prefix}tag/{slugify(t)}/">{html.escape(t)}</a>' for t in tags)

def build_post_tags(ps):
    """Fill each post's <!-- TAGS:START/END --> block with its tags, linked to the tag pages."""
    for p in ps:
        f = os.path.join(ROOT, "blog", p["slug"], "index.html")
        t = open(f, encoding="utf-8").read()
        if "<!-- TAGS:START -->" not in t:
            sys.exit(f"blog/{p['slug']}/index.html: missing the <!-- TAGS:START --><!-- TAGS:END --> block")
        new = re.sub(r"(<!-- TAGS:START -->).*?(<!-- TAGS:END -->)",
                     lambda m: m.group(1) + "Tags: " + tag_links(p["tags"], "../") + m.group(2), t, flags=re.S)
        if new != t:
            open(f, "w", encoding="utf-8").write(new)

PAGE_TAIL = """  <footer>
    <p><a href="/blog/">&#8592; All posts</a> <span class="dot">&middot;</span> <a href="/blog/feed.xml">RSS</a> <span class="dot">&middot;</span> <a href="mailto:hello@mochi-factory.com">hello@mochi-factory.com</a> <span class="dot">&middot;</span> <a href="/privacy/">Privacy</a> &middot; <a href="#" id="ptk-consent">Usage stats</a></p>
  </footer>
</div>
<script src="/assets/ptk-analytics.js" defer></script>
<script src="https://api.88eggs.com/feedback/widget.js?v=2" data-key="fk_AQATHVVwLl3BAOYwccx_nO1h" async></script>
</body>
</html>
"""

def build_tag_pages(ps):
    """One page per tag at blog/tag/<tag>/ (generated; stale tag folders are removed)."""
    tdir = os.path.join(ROOT, "blog", "tag")
    used = {}
    for p in ps:
        for t in p["tags"]:
            used.setdefault(t, []).append(p)
    keep = {slugify(t) for t in used}
    if os.path.isdir(tdir):
        for d in os.listdir(tdir):
            if d not in keep and os.path.isdir(os.path.join(tdir, d)) and os.path.isfile(os.path.join(tdir, d, "index.html")):
                os.remove(os.path.join(tdir, d, "index.html")); os.rmdir(os.path.join(tdir, d))
    for t in TAGS:
        if t not in used:
            continue
        slug = slugify(t); posts_ = used[t]
        os.makedirs(os.path.join(tdir, slug), exist_ok=True)
        n = len(posts_)
        desc = f"{n} post{'s' if n != 1 else ''} tagged {t} on the Mochi Factory blog."
        items = "\n".join(
            f'    <li><h2><a href="/blog/{q["slug"]}/">{html.escape(q["title"])}</a></h2>'
            f'<p class="post-meta"><time datetime="{q["date"]}">{q["date"]}</time></p>'
            f'<p>{html.escape(q["desc"])}</p></li>' for q in posts_)
        page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Posts tagged {html.escape(t)} &middot; Mochi Factory Blog</title>
<meta name="description" content="{html.escape(desc)}">
<link rel="canonical" href="{SITE}/blog/tag/{slug}/">
<link rel="alternate" type="application/rss+xml" title="Mochi Factory Blog" href="/blog/feed.xml">
<link rel="stylesheet" href="../../../assets/site.css">
<link rel="stylesheet" href="../../../assets/blog.css">
</head>
<body>
<div class="page">
  <header>
    <p class="eyebrow"><a href="../../../">Mochi Factory</a> &middot; <a href="../../">Blog</a></p>
    <h1 class="page-title">Tagged: {html.escape(t)}</h1>
    <p class="page-lede">{n} post{'s' if n != 1 else ''}. <a href="../../">All posts</a></p>
  </header>

  <ul class="post-list">
{items}
  </ul>

{PAGE_TAIL}"""
        open(os.path.join(tdir, slug, "index.html"), "w", encoding="utf-8").write(page)
    return used

def build_index(ps):
    f = os.path.join(ROOT, "blog", "index.html")
    t = open(f, encoding="utf-8").read()
    if ps:
        items = "\n".join(
            f'    <li><h2><a href="{p["slug"]}/">{html.escape(p["title"])}</a></h2>'
            f'<p class="post-meta"><time datetime="{p["date"]}">{p["date"]}</time></p>'
            f'<p>{html.escape(p["desc"])}</p>'
            f'<p class="post-tags">Tags: {tag_links(p["tags"], "")}</p></li>' for p in ps)
        body = f'  <ul class="post-list">\n{items}\n  </ul>'
    else:
        body = '  <p class="post-empty">The first posts are on their way.</p>'
    noindex = '<meta name="robots" content="noindex">\n'
    t = t.replace(noindex, "")
    if not ps:  # an empty blog stays out of search until the first post
        t = t.replace('<link rel="canonical"', noindex + '<link rel="canonical"', 1)
    new = re.sub(r"(<!-- POSTS:START[^>]*-->\n).*?(\n  <!-- POSTS:END -->)", lambda m: m.group(1) + body + m.group(2), t, flags=re.S)
    counts = {}
    for p in ps:
        for tg in p["tags"]:
            counts[tg] = counts.get(tg, 0) + 1
    tl = ", ".join(f'<a href="tag/{slugify(tg)}/">{html.escape(tg)}</a> ({counts[tg]})' for tg in TAGS if tg in counts)
    new = re.sub(r"(<!-- TAGLIST:START -->).*?(<!-- TAGLIST:END -->)",
                 lambda m: m.group(1) + (f'\n  <p class="tag-list">Browse by tag: {tl}</p>\n  ' if tl else "") + m.group(2), new, flags=re.S)
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
        f"<description>{html.escape(p['desc'])}</description>"
        + "".join(f"<category>{html.escape(t)}</category>" for t in p["tags"]) + "</item>" for p in ps)
    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0">\n<channel>\n'
           f'  <title>Mochi Factory Blog</title>\n  <link>{SITE}/blog/</link>\n'
           '  <description>Short, practical posts from Mochi Factory.</description>\n  <language>en-us</language>'
           f'{items}\n</channel>\n</rss>\n')
    open(os.path.join(ROOT, "blog", "feed.xml"), "w", encoding="utf-8").write(xml)

def build_sitemap(ps, used=None):
    files = subprocess.run(["git", "-C", ROOT, "ls-files", "*.html"], capture_output=True, text=True, check=True).stdout.split()
    files += [f"blog/{p['slug']}/index.html" for p in ps]
    files += [f"blog/tag/{slugify(t)}/index.html" for t in (used or {})]
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
    build_post_tags(ps); used = build_tag_pages(ps)
    build_index(ps); build_home_link(ps); build_feed(ps); build_sitemap(ps, used)
    print(f"{len(ps)} posts, {len(used)} tag pages; blog/index.html, blog/feed.xml and sitemap.xml rebuilt")
