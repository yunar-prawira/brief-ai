#!/usr/bin/env python3
"""Build statis Brief AI.

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

SITE_TITLE = "Brief AI"
SITE_TAGLINE = "Catatan harian soal AI — dan hal lain yang Yunar pedulikan."
SITE_URL = "https://yunar-prawira.github.io/brief-ai"

THEMES = {
    "ai": "#4f46e5", "dev": "#0ea5e9", "man utd": "#d92b2b", "hr": "#0d9488",
    "saas": "#7c3aed", "product": "#d97706", "indonesia": "#059669",
    "politik": "#64748b", "riset": "#db2777", "default": "#8a5a2b",
}

CSS = """
:root{
  --bg:#fcfcfb; --panel:#ffffff; --ink:#111110; --ink-2:#3d3b36; --muted:#78736a;
  --line:#e8e4db; --line-soft:#f1eee7; --c:#4f46e5;
  --sans:ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
  --serif:ui-serif,Georgia,"Iowan Old Style","Times New Roman",serif;
  --mono:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
  --r:14px;
}
@media (prefers-color-scheme: dark){
  :root{ --bg:#0d0d0c; --panel:#151513; --ink:#f2f0ea; --ink-2:#cdc9c0; --muted:#98938a;
         --line:#272621; --line-soft:#1d1c19; }
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0; background:var(--bg); color:var(--ink); font-family:var(--sans);
  font-size:17px; line-height:1.6; letter-spacing:-.005em; -webkit-font-smoothing:antialiased}
a{color:inherit}
.wrap{max-width:920px; margin:0 auto; padding:0 20px}
.bar{position:sticky; top:0; z-index:9; border-bottom:1px solid var(--line-soft);
  background:var(--bg)}
.bar-in{display:flex; align-items:center; gap:16px; height:56px}
.logo{display:flex; align-items:center; gap:9px; text-decoration:none; font-weight:650;
  letter-spacing:-.02em; font-size:.98rem}
.logo .dot{width:9px; height:9px; border-radius:50%; background:var(--c);
  box-shadow:0 0 0 4px color-mix(in srgb, var(--c) 16%, transparent)}
.bar nav{margin-left:auto; display:flex; gap:18px; font-size:.82rem; color:var(--muted)}
.bar nav a{text-decoration:none}
.bar nav a:hover{color:var(--ink)}
.hero{margin:36px 0 8px}
.kicker{display:flex; flex-wrap:wrap; align-items:center; gap:8px; margin-bottom:14px;
  font-size:.71rem; letter-spacing:.09em; text-transform:uppercase; font-weight:650; color:var(--muted)}
.pill{display:inline-flex; align-items:center; padding:4px 10px; border-radius:999px;
  background:color-mix(in srgb, var(--c) 10%, transparent); color:var(--c); text-decoration:none;
  font-size:.71rem; font-weight:650; letter-spacing:.06em; text-transform:uppercase;
  border:1px solid color-mix(in srgb, var(--c) 22%, transparent)}
.pill:hover{background:color-mix(in srgb, var(--c) 18%, transparent)}
.hero h1{font-size:clamp(1.85rem, 5.2vw, 2.7rem); line-height:1.09; letter-spacing:-.035em;
  margin:0 0 14px; font-weight:690}
.hero h1 a{text-decoration:none}
.hero h1 a:hover{color:var(--c)}
.hero p.lede{font-size:1.05rem; color:var(--ink-2); margin:0 0 20px; max-width:62ch;
  font-family:var(--serif); line-height:1.6}
.cta{display:inline-flex; align-items:center; gap:8px; font-size:.85rem; font-weight:620;
  text-decoration:none; padding:9px 15px; border-radius:999px; border:1px solid var(--line);
  background:var(--panel); transition:.16s}
.cta:hover{border-color:var(--c); color:var(--c); transform:translateY(-1px)}
.rail{display:flex; gap:8px; overflow-x:auto; padding:24px 0 18px; border-bottom:1px solid var(--line-soft);
  scrollbar-width:none}
.rail::-webkit-scrollbar{display:none}
.rail a{white-space:nowrap; font-size:.79rem; font-weight:620; color:var(--muted);
  text-decoration:none; padding:6px 12px; border-radius:999px; border:1px solid var(--line)}
.rail a:hover{color:var(--c); border-color:var(--c)}
h2.sec{font-size:.72rem; letter-spacing:.14em; text-transform:uppercase; color:var(--muted);
  margin:40px 0 0; font-weight:700}
.grid{display:grid; gap:1px; background:var(--line); border:1px solid var(--line);
  border-radius:var(--r); overflow:hidden; margin-top:16px}
@media (min-width:720px){ .grid{grid-template-columns:1fr 1fr} }
.card{background:var(--panel); padding:24px 22px 26px; text-decoration:none; display:block;
  position:relative; transition:background .16s}
.card:hover{background:color-mix(in srgb, var(--c) 4%, var(--panel))}
.card::before{content:""; position:absolute; left:0; top:0; bottom:0; width:2px;
  background:var(--c); opacity:0; transition:opacity .16s}
.card:hover::before{opacity:1}
.card .meta{font-size:.69rem; letter-spacing:.09em; text-transform:uppercase; color:var(--muted);
  font-weight:640; display:flex; gap:8px; align-items:center; margin-bottom:9px}
.card .meta .d{width:6px; height:6px; border-radius:50%; background:var(--c); flex:none}
.card h3{margin:0 0 7px; font-size:1.08rem; line-height:1.28; letter-spacing:-.02em; font-weight:650}
.card p{margin:0; color:var(--muted); font-size:.89rem; line-height:1.5;
  display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; overflow:hidden}
article.post{max-width:660px; margin:40px auto 0}
article.post h1{font-size:clamp(1.72rem, 4.6vw, 2.45rem); line-height:1.12;
  letter-spacing:-.035em; margin:8px 0 14px; font-weight:690}
article.post .lede{font-family:var(--serif); font-size:1.08rem; color:var(--ink-2);
  margin:0 0 26px; padding-bottom:24px; border-bottom:1px solid var(--line-soft)}
.body{font-family:var(--serif); font-size:1.08rem; line-height:1.72; color:var(--ink)}
.body h2{font-family:var(--sans); font-size:1.22rem; letter-spacing:-.02em; margin:2.3em 0 .5em;
  font-weight:670; line-height:1.3}
.body h3{font-family:var(--sans); font-size:1rem; margin:1.8em 0 .4em; font-weight:670}
.body p{margin:0 0 1.15em}
.body strong{font-weight:680}
.body ul,.body ol{margin:0 0 1.25em; padding-left:1.15em}
.body li{margin:.4em 0}
.body li::marker{color:var(--c)}
.body a{color:var(--c); text-decoration:none;
  border-bottom:1px solid color-mix(in srgb, var(--c) 34%, transparent)}
.body a:hover{background:color-mix(in srgb, var(--c) 10%, transparent)}
.body blockquote{margin:1.5em 0; padding:4px 0 4px 18px; border-left:2px solid var(--c);
  color:var(--ink-2); font-style:italic}
.body hr{border:0; border-top:1px solid var(--line); margin:2.6em 0}
.body code{font-family:var(--mono); font-size:.85em; background:var(--line-soft);
  padding:.12em .38em; border-radius:4px}
.body img{max-width:100%; border-radius:10px}
.pager{display:grid; gap:1px; background:var(--line); border:1px solid var(--line);
  border-radius:var(--r); overflow:hidden; margin:56px 0 0; grid-template-columns:1fr 1fr}
.pager a{background:var(--panel); padding:16px 18px; text-decoration:none; font-size:.85rem}
.pager a span{display:block; font-size:.67rem; letter-spacing:.1em; text-transform:uppercase;
  color:var(--muted); margin-bottom:5px; font-weight:650}
.pager a strong{font-weight:630; line-height:1.35; display:block}
.pager a:hover{background:var(--line-soft)}
.pager a.next{text-align:right}
footer.site{margin:72px 0 0; border-top:1px solid var(--line-soft); padding:22px 0 60px;
  font-size:.77rem; color:var(--muted); display:flex; flex-wrap:wrap; gap:10px;
  justify-content:space-between}
footer.site a{color:var(--muted); text-decoration:none}
footer.site a:hover{color:var(--ink)}
"""


def slugify(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-") or "lain"


def theme_of(tags):
    for t in tags:
        c = THEMES.get(t.lower())
        if c:
            return c
    return THEMES["default"]


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
<link rel="alternate" type="application/rss+xml" title="{esc(SITE_TITLE)}" href="{SITE_URL}/feed.xml">
<style>{CSS}</style>
</head>
<body style="{css_vars}">
<div class="bar"><div class="wrap bar-in">
  <a class="logo" href="{SITE_URL}/"><span class="dot"></span>Brief AI</a>
  <nav><a href="{SITE_URL}/">Arsip</a><a href="{SITE_URL}/feed.xml">RSS</a></nav>
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
        c = THEMES.get(t.lower(), THEMES["default"])
        out.append(f'<a class="pill" style="--c:{c}" href="{SITE_URL}/tag/{slugify(t)}.html">'
                   f'{esc(t)}</a>')
    return "".join(out)


def card_html(it):
    meta = it["meta"]
    label = human_date(it["date"])
    if meta.get("edisi"):
        label = f"Edisi {esc(meta['edisi'])} · {label}"
    tag = it["tags"][0] if it["tags"] else ""
    tagbit = f"<span>{esc(tag)}</span>" if tag else ""
    return f"""<a class="card" style="--c:{it['color']}" href="{SITE_URL}/{it['slug']}.html">
<div class="meta"><span class="d"></span>{tagbit}<span>{label}</span></div>
<h3>{esc(meta['title'])}</h3>
<p>{esc(meta.get('ringkas',''))}</p>
</a>"""


def build():
    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "tag").mkdir(parents=True)
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
                 css_vars=f"--c:{it['color']}", desc=meta.get("ringkas")),
            encoding="utf-8")

    by_tag = {}
    for it in items:
        for t in it["tags"]:
            by_tag.setdefault(t, []).append(it)
    for t, group in by_tag.items():
        c = THEMES.get(t.lower(), THEMES["default"])
        body = (f'<section class="hero" style="--c:{c}"><div class="kicker"><span>Topik</span></div>'
                f'<h1>{esc(t)}</h1><p class="lede">{len(group)} tulisan.</p></section>'
                f'<div class="grid">{"".join(card_html(x) for x in group)}</div>')
        (OUT / "tag" / f"{slugify(t)}.html").write_text(
            page(f"{t} — {SITE_TITLE}", body, css_vars=f"--c:{c}"), encoding="utf-8")

    if items:
        top = items[0]
        hero_bits = [human_date(top["date"])]
        if top["meta"].get("edisi"):
            hero_bits.insert(0, f"Edisi {esc(top['meta']['edisi'])}")
        hero = f"""<section class="hero" style="--c:{top['color']}">
<div class="kicker">{tag_pills(top, 2)}<span>{" · ".join(hero_bits)}</span></div>
<h1><a href="{SITE_URL}/{top['slug']}.html">{esc(top['meta']['title'])}</a></h1>
<p class="lede">{esc(top['meta'].get('ringkas',''))}</p>
<a class="cta" href="{SITE_URL}/{top['slug']}.html">Baca edisi ini
<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"
 stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h13M12 5l7 7-7 7"/></svg></a>
</section>"""
        rest = items[1:]
        grid = (f'<h2 class="sec">Edisi sebelumnya</h2><div class="grid">'
                f'{"".join(card_html(x) for x in rest)}</div>') if rest else ""
    else:
        hero = '<section class="hero"><h1>Belum ada edisi</h1></section>'
        grid = ""
    rail = "".join(
        f'<a style="--c:{THEMES.get(t.lower(), THEMES["default"])}" '
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
