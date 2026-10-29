#!/usr/bin/env python3
"""Build statis untuk blog Brief AI.

posts/*.md  ->  docs/index.html, docs/<slug>.html, docs/feed.xml

Frontmatter wajib:
---
title: Judul
date: 2026-10-29
edisi: 01            (opsional)
tag: Laporan         (opsional)
ringkas: satu paragraf ringkas untuk daftar & RSS
---
"""
import html
import re
import shutil
from datetime import date, datetime, timezone
from email.utils import format_datetime
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent
POSTS = ROOT / "posts"
OUT = ROOT / "docs"

SITE_TITLE = "Brief AI"
SITE_TAGLINE = "Kurasi berita & laporan AI, ditulis untuk dibaca Yunar."
SITE_URL = "https://yunar-prawira.github.io/brief-ai"

CSS = """
:root{
  --bg:#fbfaf7; --ink:#191919; --muted:#6f6a61; --rule:#e3ded4;
  --accent:#8a5a2b; --card:#ffffff;
}
@media (prefers-color-scheme: dark){
  :root{ --bg:#14140f; --ink:#eceae3; --muted:#9c968a; --rule:#2c2b24;
         --accent:#d9a86c; --card:#1b1b15; }
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{
  margin:0; background:var(--bg); color:var(--ink);
  font-family:ui-serif,Georgia,"Iowan Old Style","Times New Roman",serif;
  font-size:19px; line-height:1.68;
}
.wrap{max-width:680px; margin:0 auto; padding:0 22px 96px}
header.site{padding:34px 0 26px; border-bottom:1px solid var(--rule); margin-bottom:44px}
header.site a.home{color:var(--ink); text-decoration:none; display:inline-block}
.brand{font-size:1.02rem; letter-spacing:.22em; text-transform:uppercase; font-weight:600}
.tagline{color:var(--muted); font-size:.92rem; margin-top:6px; font-family:ui-sans-serif,system-ui,sans-serif}
nav.top{margin-top:14px; font-family:ui-sans-serif,system-ui,sans-serif; font-size:.82rem;
  letter-spacing:.04em; text-transform:uppercase}
nav.top a{color:var(--muted); text-decoration:none; margin-right:18px}
nav.top a:hover{color:var(--accent)}
h1,h2,h3{line-height:1.25; font-weight:600; letter-spacing:-.01em}
h1{font-size:1.92rem; margin:0 0 10px}
h2{font-size:1.22rem; margin:2.1em 0 .6em}
h3{font-size:1.04rem; margin:1.7em 0 .4em}
p{margin:0 0 1.15em}
a{color:var(--accent); text-underline-offset:3px}
ul,ol{margin:0 0 1.2em; padding-left:1.25em}
li{margin:.35em 0}
blockquote{margin:1.4em 0; padding:.2em 0 .2em 18px; border-left:2px solid var(--rule);
  color:var(--muted); font-style:italic}
hr{border:0; border-top:1px solid var(--rule); margin:2.4em 0}
.meta{font-family:ui-sans-serif,system-ui,sans-serif; font-size:.78rem; letter-spacing:.06em;
  text-transform:uppercase; color:var(--muted); margin-bottom:12px}
.meta .dot{opacity:.5; margin:0 7px}
.lede{color:var(--muted); font-size:1.02rem; margin-bottom:2.2em}
article ol,article ul{font-size:1rem}
code{font-family:ui-monospace,SFMono-Regular,Menlo,monospace; font-size:.86em;
  background:var(--rule); padding:.1em .35em; border-radius:3px}
img{max-width:100%; height:auto; border-radius:4px}
.list{list-style:none; padding:0; margin:0}
.list li{padding:22px 0; border-bottom:1px solid var(--rule); margin:0}
.list li:first-child{padding-top:0}
.list a.title{font-size:1.18rem; color:var(--ink); text-decoration:none; font-weight:600}
.list a.title:hover{color:var(--accent)}
.list .ringkas{color:var(--muted); font-size:.95rem; margin-top:6px}
footer.site{border-top:1px solid var(--rule); margin-top:60px; padding-top:20px;
  font-family:ui-sans-serif,system-ui,sans-serif; font-size:.8rem; color:var(--muted)}
footer.site a{color:var(--muted)}
.back{font-family:ui-sans-serif,system-ui,sans-serif; font-size:.82rem; margin-top:46px}
.back a{color:var(--muted); text-decoration:none}
"""


def parse_front(text: str):
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", text, re.S)
    if not m:
        raise ValueError("frontmatter tidak ditemukan")
    meta = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            v = v.strip()
            if len(v) > 1 and v[0] == v[-1] and v[0] in "\"'":
                v = v[1:-1]
            meta[k.strip()] = v
    return meta, m.group(2)


def esc(s: str) -> str:
    return html.escape(s, quote=True)


def page(title, body, extra_head=""):
    return f"""<!doctype html>
<html lang="id">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(SITE_TAGLINE)}">
<link rel="alternate" type="application/rss+xml" title="{esc(SITE_TITLE)}" href="{SITE_URL}/feed.xml">
<style>{CSS}</style>
{extra_head}
</head>
<body>
<div class="wrap">
<header class="site">
  <a class="home" href="{SITE_URL}/"><span class="brand">{esc(SITE_TITLE)}</span></a>
  <div class="tagline">{esc(SITE_TAGLINE)}</div>
  <nav class="top"><a href="{SITE_URL}/">Arsip</a><a href="{SITE_URL}/feed.xml">RSS</a></nav>
</header>
{body}
<footer class="site">
  Ditulis &amp; dirawat otomatis oleh Rina. Sumber selalu ditautkan di tiap tulisan.
  &nbsp;·&nbsp; <a href="{SITE_URL}/feed.xml">feed.xml</a>
</footer>
</div>
</body>
</html>
"""


def human_date(d: date) -> str:
    bulan = ["Januari","Februari","Maret","April","Mei","Juni","Juli","Agustus",
             "September","Oktober","November","Desember"]
    return f"{d.day} {bulan[d.month-1]} {d.year}"


def build():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)

    items = []
    for p in sorted(POSTS.glob("*.md")):
        meta, body_md = parse_front(p.read_text(encoding="utf-8"))
        slug = p.stem
        dt = datetime.strptime(meta["date"], "%Y-%m-%d").date()
        items.append({"slug": slug, "meta": meta, "md": body_md, "date": dt})
    items.sort(key=lambda x: x["date"], reverse=True)

    # halaman post
    for it in items:
        meta = it["meta"]
        body_html = markdown.markdown(it["md"], extensions=["extra", "sane_lists"])
        bits = [human_date(it["date"])]
        if meta.get("edisi"):
            bits.insert(0, f"Edisi {esc(meta['edisi'])}")
        if meta.get("tag"):
            bits.append(esc(meta["tag"]))
        meta_line = '<span class="dot">·</span>'.join(bits)
        body = f"""<article>
<div class="meta">{meta_line}</div>
<h1>{esc(meta['title'])}</h1>
<p class="lede">{esc(meta.get('ringkas',''))}</p>
{body_html}
<div class="back"><a href="{SITE_URL}/">&larr; Semua edisi</a></div>
</article>"""
        (OUT / f"{it['slug']}.html").write_text(
            page(f"{meta['title']} — {SITE_TITLE}", body), encoding="utf-8")

    # index
    lis = []
    for it in items:
        meta = it["meta"]
        label = human_date(it["date"])
        if meta.get("edisi"):
            label = f"Edisi {esc(meta['edisi'])} · {label}"
        lis.append(f"""<li>
<div class="meta">{label}</div>
<a class="title" href="{SITE_URL}/{it['slug']}.html">{esc(meta['title'])}</a>
<div class="ringkas">{esc(meta.get('ringkas',''))}</div>
</li>""")
    body = "<ul class=\"list\">\n" + "\n".join(lis) + "\n</ul>"
    (OUT / "index.html").write_text(page(SITE_TITLE, body), encoding="utf-8")

    # RSS
    entries = []
    for it in items[:30]:
        meta = it["meta"]
        link = f"{SITE_URL}/{it['slug']}.html"
        entries.append(f"""<item>
<title>{esc(meta['title'])}</title>
<link>{link}</link>
<guid isPermaLink="true">{link}</guid>
<pubDate>{format_datetime(datetime.combine(it['date'], datetime.min.time(), tzinfo=timezone.utc))}</pubDate>
<description>{esc(meta.get('ringkas',''))}</description>
</item>""")
    feed = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel>
<title>{esc(SITE_TITLE)}</title>
<link>{SITE_URL}/</link>
<description>{esc(SITE_TAGLINE)}</description>
<language>id</language>
<lastBuildDate>{format_datetime(datetime.now(timezone.utc))}</lastBuildDate>
{''.join(entries)}
</channel></rss>
"""
    (OUT / "feed.xml").write_text(feed, encoding="utf-8")
    (OUT / ".nojekyll").write_text("", encoding="utf-8")
    print(f"built {len(items)} post -> {OUT}")


if __name__ == "__main__":
    build()
