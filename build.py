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
import json
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
SITE_TAGLINE = "Catatan soal AI tiga kali seminggu — dan hal lain yang Yunar pedulikan."
SITE_URL = "https://kilas.yunarprawira.com"
SITE_HOST = "kilas.yunarprawira.com"  # ditulis ke docs/CNAME untuk GitHub Pages

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


def darken(hex_color: str, factor: float) -> str:
    """Campur warna tema ke arah hitam supaya teks putih di atasnya lolos kontras."""
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return "#{:02x}{:02x}{:02x}".format(*(int(v * factor) for v in (r, g, b)))


def css_vars(color_pair) -> str:
    c, c2 = color_pair
    return (f"--c:{c};--c2:{c2}"
            f";--c-ink:{darken(c, 0.58)}"          # teks pil/topik: >=4.5:1 di latar terang
            f";--c-cta1:{darken(c, 0.86)}"          # stop gradien CTA (teks putih)
            f";--c-cta2:{darken(c2, 0.50)}")


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


def abs_url(path: str) -> str:
    """URL absolut untuk canonical / sitemap / JSON-LD."""
    return SITE_URL + (path if path.startswith("/") else "/" + path)


def squeeze(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip()


def page(title, body, css_vars="", desc=None, path="/", og_type="website", ld=None):
    canon = abs_url(path)
    desc = squeeze(desc or SITE_TAGLINE)
    ld_html = (f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>'
               if ld else "")
    return f"""<!doctype html>
<html lang="id">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<meta name="color-scheme" content="light dark">
<meta name="robots" content="index,follow,max-image-preview:large">
<link rel="canonical" href="{esc(canon)}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:type" content="{esc(og_type)}">
<meta property="og:url" content="{esc(canon)}">
<meta property="og:site_name" content="{esc(SITE_TITLE)}">
<meta property="og:locale" content="id_ID">
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="{esc(title)}">
<meta name="twitter:description" content="{esc(desc)}">
{ld_html}
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


def write_sitemap(items, by_tag):
    """sitemap.xml: beranda + semua edisi + halaman topik."""
    rows = []
    today = date.today().isoformat()
    newest = items[0]["date"].isoformat() if items else today
    rows.append((abs_url("/"), newest, "daily", "1.0"))
    for it in items:
        rows.append((abs_url(f"/{it['slug']}.html"), it["date"].isoformat(), "monthly", "0.8"))
    for t, group in by_tag.items():
        last = max(x["date"] for x in group).isoformat()
        rows.append((abs_url(f"/tag/{slugify(t)}.html"), last, "weekly", "0.5"))
    body = "\n".join(
        f"  <url><loc>{esc(u)}</loc><lastmod>{m}</lastmod>"
        f"<changefreq>{c}</changefreq><priority>{p}</priority></url>"
        for u, m, c, p in rows)
    (OUT / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{body}\n</urlset>\n", encoding="utf-8")
    return len(rows)


def write_robots():
    """robots.txt: izinkan crawl biasa + asisten AI (supaya edisi bisa dikutip)."""
    bots = ["GPTBot", "OAI-SearchBot", "ChatGPT-User", "PerplexityBot", "Perplexity-User",
            "ClaudeBot", "Claude-SearchBot", "Claude-User", "Googlebot", "Bingbot",
            "Google-Extended", "Applebot", "CCBot"]
    lines = ["User-agent: *", "Allow: /", ""]
    for b in bots:
        lines += [f"User-agent: {b}", "Allow: /", ""]
    lines += [f"Sitemap: {abs_url('/sitemap.xml')}", ""]
    (OUT / "robots.txt").write_text("\n".join(lines), encoding="utf-8")


def write_llms(items, by_tag):
    """llms.txt: peta ringkas situs untuk asisten AI (llmstxt.org)."""
    out = [
        f"# {SITE_TITLE}",
        "",
        f"> {SITE_TAGLINE}",
        "",
        "Blog berbahasa Indonesia: tiga edisi per minggu berisi ringkasan berita AI "
        "pilihan, dengan tautan sumber di setiap klaim. Ditulis dan dirawat otomatis.",
        "",
        f"- RSS: {abs_url('/feed.xml')}",
        f"- Sitemap: {abs_url('/sitemap.xml')}",
        "- Kutipan diperbolehkan dengan atribusi dan tautan ke edisi aslinya.",
        "",
        "## Edisi",
        "",
    ]
    for it in items:
        meta = it["meta"]
        label = ""
        if meta.get("edisi") and not meta["title"].lower().startswith("edisi"):
            label = f"Edisi {meta['edisi']} — "
        ringkas = squeeze(meta.get("ringkas", ""))
        line = f"- [{label}{meta['title']}]({abs_url('/' + it['slug'] + '.html')})"
        line += f" — {human_date(it['date'])}"
        if ringkas:
            line += f": {ringkas}"
        out.append(line)
    if by_tag:
        out += ["", "## Topik", ""]
        for t in sorted(by_tag, key=lambda x: (-len(by_tag[x]), x)):
            out.append(f"- [{t}]({abs_url('/tag/' + slugify(t) + '.html')}): "
                       f"{len(by_tag[t])} tulisan")
    (OUT / "llms.txt").write_text("\n".join(out) + "\n", encoding="utf-8")


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
        post_url = abs_url(f"/{it['slug']}.html")
        ld = {
            "@context": "https://schema.org",
            "@type": "BlogPosting",
            "headline": meta["title"],
            "description": squeeze(meta.get("ringkas", "")),
            "datePublished": it["date"].isoformat(),
            "dateModified": it["date"].isoformat(),
            "inLanguage": "id",
            "url": post_url,
            "mainEntityOfPage": post_url,
            "author": {"@type": "Person", "name": "Yunar Prawira Negara",
                       "url": "https://github.com/yunar-prawira"},
            "publisher": {"@type": "Person", "name": "Yunar Prawira Negara"},
            "isPartOf": {"@type": "Blog", "name": SITE_TITLE, "url": abs_url("/")},
        }
        if it["tags"]:
            ld["keywords"] = ", ".join(it["tags"])
            ld["articleSection"] = it["tags"][0]
        (OUT / f"{it['slug']}.html").write_text(
            page(f"{meta['title']} — {SITE_TITLE}", body,
                 css_vars=css_vars(it["color"]), desc=meta.get("ringkas"),
                 path=f"/{it['slug']}.html", og_type="article", ld=ld),
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
            page(f"{t} — {SITE_TITLE}", body, css_vars=css_vars(pair),
                 desc=f"{len(group)} tulisan bertopik {t} di {SITE_TITLE}.",
                 path=f"/tag/{slugify(t)}.html"), encoding="utf-8")

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
    blog_ld = {
        "@context": "https://schema.org",
        "@type": "Blog",
        "name": SITE_TITLE,
        "description": SITE_TAGLINE,
        "url": abs_url("/"),
        "inLanguage": "id",
        "author": {"@type": "Person", "name": "Yunar Prawira Negara"},
        "blogPost": [
            {"@type": "BlogPosting", "headline": x["meta"]["title"],
             "url": abs_url(f"/{x['slug']}.html"),
             "datePublished": x["date"].isoformat(),
             "description": squeeze(x["meta"].get("ringkas", ""))}
            for x in items[:10]
        ],
    }
    (OUT / "index.html").write_text(
        page(SITE_TITLE, hero + rail + grid, desc=SITE_TAGLINE, path="/", ld=blog_ld),
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
    n_urls = write_sitemap(items, by_tag)
    write_robots()
    write_llms(items, by_tag)
    (OUT / ".nojekyll").write_text("", encoding="utf-8")
    (OUT / "CNAME").write_text(SITE_HOST + "\n", encoding="utf-8")
    print(f"built {len(items)} post, {len(by_tag)} topik, {n_urls} url sitemap -> {OUT}")


if __name__ == "__main__":
    build()
