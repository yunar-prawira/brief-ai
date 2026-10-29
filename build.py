#!/usr/bin/env python3
"""Build statis Yunar AI Brief.

posts/*.md -> docs/index.html, docs/<slug>.html, docs/tag/<tag>.html, docs/feed.xml

Frontmatter:
---
title: Judul
date: 2026-10-29
edisi: 02                     (opsional)
tag: AI, HR                   (opsional, boleh lebih dari satu; yang pertama jadi warna utama)
ringkas: satu paragraf ringkas untuk kartu & RSS
---
"""
import html
import re
import shutil
import unicodedata
from datetime import date, datetime, timezone
from email.utils import format_datetime
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent
POSTS = ROOT / "posts"
OUT = ROOT / "docs"
STYLE = ROOT / "style.css"

SITE_TITLE = "Yunar AI Brief"
SITE_TAGLINE = "Catatan harian soal AI — dan hal lain yang Yunar pedulikan."
SITE_URL = "https://yunar-prawira.github.io/brief-ai"

# topik -> (warna utama, warna gradien)
THEMES = {
    "ai": ("#4f46e5", "#06b6d4"),
    "dev": ("#0284c7", "#6366f1"),
    "man utd": ("#dc2626", "#f59e0b"),
    "hr": ("#0d9488", "#22c55e"),
    "saas": ("#7c3aed", "#ec4899"),
    "product": ("#ea580c", "#f59e0b"),
    "indonesia": ("#e11d48", "#f97316"),
    "politik": ("#475569", "#0ea5e9"),
    "riset": ("#db2777", "#8b5cf6"),
    "default": ("#8a5a2b", "#d97706"),
}

THEME_JS = """
(function(){try{var t=localStorage.getItem('yab-theme');if(t)document.documentElement.dataset.theme=t;}catch(e){}})();
function yabToggle(){var d=document.documentElement;
  var cur=d.dataset.theme||(window.matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light');
  var nx=cur==='dark'?'light':'dark';d.dataset.theme=nx;
  try{localStorage.setItem('yab-theme',nx);}catch(e){}}
"""

TG_ICON = ('<svg class="i-sun" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
           'stroke-linecap="round"><circle cx="12" cy="12" r="4.2"/><path d="M12 2.6v2.2M12 19.2v2.2'
           'M2.6 12h2.2M19.2 12h2.2M5.4 5.4l1.6 1.6M17 17l1.6 1.6M18.6 5.4L17 7M7 17l-1.6 1.6"/></svg>'
           '<svg class="i-moon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
           'stroke-linecap="round" stroke-linejoin="round"><path d="M20 14.5A8.5 8.5 0 1 1 9.5 4a7 7 0 0 0 10.5 10.5Z"/></svg>')


def slugify(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-") or "lain"


def theme_of(tags):
    for t in tags:
        c = THEMES.get(t.lower())
        if c:
            return c
    return THEMES["default"]


def css_vars(color_pair) -> str:
    return f"--c:{color_pair[0]};--c2:{color_pair[1]}"


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


def page(title, body, css_vars="", desc=None):
    return f"""<!doctype html>
<html lang="id">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc or SITE_TAGLINE)}">
<meta name="color-scheme" content="light dark">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc or SITE_TAGLINE)}">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><rect width='100' height='100' rx='28' fill='%234f46e5'/></svg>">
<link rel="alternate" type="application/rss+xml" title="{esc(SITE_TITLE)}" href="{SITE_URL}/feed.xml">
<link rel="stylesheet" href="{SITE_URL}/style.css">
<script>{THEME_JS}</script>
</head>
<body style="{css_vars}">
<div class="bar"><div class="wrap bar-in">
  <a class="logo" href="{SITE_URL}/"><span class="mark"></span>{esc(SITE_TITLE)}</a>
  <nav>
    <a href="{SITE_URL}/">Arsip</a>
    <a href="{SITE_URL}/feed.xml">RSS</a>
    <button class="tg" type="button" onclick="yabToggle()" aria-label="Ganti tema terang atau gelap">{TG_ICON}</button>
  </nav>
</div></div>
<div class="wrap">
{body}
<footer class="site">
  <span>Ditulis &amp; dirawat otomatis oleh Rina · sumber selalu ditautkan.</span>
  <a href="{SITE_URL}/feed.xml">feed.xml</a>
</footer>
</div>
</body>
</html>
"""


BULAN = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus",
         "September", "Oktober", "November", "Desember"]


def human_date(d: date) -> str:
    return f"{d.day} {BULAN[d.month-1]} {d.year}"


def load():
    items = []
    for p in sorted(POSTS.glob("*.md")):
        meta, body_md = parse_front(p.read_text(encoding="utf-8"))
        dt = datetime.strptime(meta["date"], "%Y-%m-%d").date()
        tags = [t.strip() for t in meta.get("tag", "").split(",") if t.strip()]
        items.append({"slug": p.stem, "meta": meta, "md": body_md, "date": dt,
                      "tags": tags, "color": theme_of(tags)})
    items.sort(key=lambda x: (x["date"], x["slug"]), reverse=True)
    return items


def tag_pills(item, limit=2):
    out = []
    for t in item["tags"][:limit]:
        out.append(f'<a class="pill" style="{css_vars(THEMES.get(t.lower(), THEMES["default"]))}" '
                   f'href="{SITE_URL}/tag/{slugify(t)}.html">{esc(t)}</a>')
    return "".join(out)


def card_html(it):
    meta = it["meta"]
    label = human_date(it["date"])
    if meta.get("edisi"):
        label = f"Edisi {esc(meta['edisi'])} · {label}"
    tag = it["tags"][0] if it["tags"] else ""
    tagbit = f"<span>{esc(tag)}</span>" if tag else ""
    return f"""<a class="card" style="{css_vars(it['color'])}" href="{SITE_URL}/{it['slug']}.html">
<div class="meta"><span class="d"></span>{tagbit}<span>{label}</span></div>
<h3>{esc(meta['title'])}</h3>
<p>{esc(meta.get('ringkas',''))}</p>
</a>"""


def build():
    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "tag").mkdir(parents=True)
    shutil.copy(STYLE, OUT / "style.css")
    items = load()

    for i, it in enumerate(items):
        meta = it["meta"]
        body_html = markdown.markdown(it["md"], extensions=["extra", "sane_lists"])
        bits = [human_date(it["date"])]
        if meta.get("edisi"):
            bits.insert(0, f"Edisi {esc(meta['edisi'])}")
        newer = items[i-1] if i > 0 else None
        older = items[i+1] if i+1 < len(items) else None
        cells = []
        cells.append(f'<a class="next" href="{SITE_URL}/{newer["slug"]}.html"><span>Lebih baru</span>'
                     f'<strong>{esc(newer["meta"]["title"])}</strong></a>' if newer else "<span></span>")
        cells.append(f'<a href="{SITE_URL}/{older["slug"]}.html"><span>Lebih lama</span>'
                     f'<strong>{esc(older["meta"]["title"])}</strong></a>' if older else "<span></span>")
        pager = f'<div class="pager">{"".join(cells)}</div>' if (newer or older) else ""
        body = f"""<article class="post">
<div class="kicker">{tag_pills(it, 3)}<span>{" · ".join(bits)}</span></div>
<h1>{esc(meta['title'])}</h1>
<p class="lede">{esc(meta.get('ringkas',''))}</p>
<div class="body">{body_html}</div>
{pager}
</article>"""
        (OUT / f"{it['slug']}.html").write_text(
            page(f"{meta['title']} — {SITE_TITLE}", body,
                 css_vars=css_vars(it["color"]), desc=meta.get("ringkas")),
            encoding="utf-8")

    by_tag = {}
    for it in items:
        for t in it["tags"]:
            by_tag.setdefault(t, []).append(it)
    for t, group in by_tag.items():
        pair = THEMES.get(t.lower(), THEMES["default"])
        body = (f'<section class="hero" style="{css_vars(pair)}">'
                f'<div class="kicker"><span>Topik</span></div>'
                f'<h1>{esc(t)}</h1><p class="lede">{len(group)} tulisan.</p></section>'
                f'<div class="grid">{"".join(card_html(x) for x in group)}</div>')
        (OUT / "tag" / f"{slugify(t)}.html").write_text(
            page(f"{t} — {SITE_TITLE}", body, css_vars=css_vars(pair)), encoding="utf-8")

    if items:
        top = items[0]
        hero_bits = [human_date(top["date"])]
        if top["meta"].get("edisi"):
            hero_bits.insert(0, f"Edisi {esc(top['meta']['edisi'])}")
        hero = f"""<section class="hero" style="{css_vars(top['color'])}">
<div class="kicker">{tag_pills(top, 2)}<span>{" · ".join(hero_bits)}</span></div>
<h1><a href="{SITE_URL}/{top['slug']}.html">{esc(top['meta']['title'])}</a></h1>
<p class="lede">{esc(top['meta'].get('ringkas',''))}</p>
<a class="cta" href="{SITE_URL}/{top['slug']}.html">Baca edisi ini
<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4"
 stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h13M12 5l7 7-7 7"/></svg></a>
</section>"""
        rest = items[1:]
        grid = (f'<h2 class="sec">Edisi sebelumnya</h2><div class="grid">'
                f'{"".join(card_html(x) for x in rest)}</div>') if rest else ""
    else:
        hero = '<section class="hero"><h1>Belum ada edisi</h1></section>'
        grid = ""
    rail = "".join(
        f'<a style="{css_vars(THEMES.get(t.lower(), THEMES["default"]))}" '
        f'href="{SITE_URL}/tag/{slugify(t)}.html">{esc(t)}</a>'
        for t in sorted(by_tag, key=lambda x: (-len(by_tag[x]), x)))
    rail = f'<div class="rail">{rail}</div>' if rail else ""
    (OUT / "index.html").write_text(page(SITE_TITLE, hero + rail + grid, desc=SITE_TAGLINE),
                                    encoding="utf-8")

    entries = []
    for it in items[:40]:
        link = f"{SITE_URL}/{it['slug']}.html"
        entries.append(f"""<item>
<title>{esc(it['meta']['title'])}</title>
<link>{link}</link>
<guid isPermaLink="true">{link}</guid>
<pubDate>{format_datetime(datetime.combine(it['date'], datetime.min.time(), tzinfo=timezone.utc))}</pubDate>
<description>{esc(it['meta'].get('ringkas',''))}</description>
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
    print(f"built {len(items)} post, {len(by_tag)} topik -> {OUT}")


if __name__ == "__main__":
    build()
