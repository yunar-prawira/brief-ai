#!/usr/bin/env python3
"""Uji build.py: python3 test_build.py"""
import shutil
import subprocess
import sys
import tempfile
import json
import re
import xml.etree.ElementTree as ET
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent

SITE = "https://yunar-prawira.github.io/brief-ai"


def ld_json(html_text):
    """Ambil blok JSON-LD pertama dari sebuah halaman dan parse jadi dict."""
    m = re.search(r'<script type="application/ld\+json">(.*?)</script>', html_text, re.S)
    return json.loads(m.group(1)) if m else None

FIXTURES = {
    "2026-01-05-lama.md": '---\ntitle: "Yang Lama"\ndate: 2026-01-05\nedisi: "01"\ntag: "AI"\n'
                          'ringkas: "post lama"\n---\nIsi **lama** dengan `kode`.\n',
    "2026-03-10-baru.md": '---\ntitle: "Yang Baru"\ndate: 2026-03-10\nedisi: "02"\ntag: "Man Utd, SaaS"\n'
                          'ringkas: "post baru <dengan & tanda>"\n---\n- satu\n- dua\n',
}

THEME_BARU = "#dc2626"  # tag pertama "Man Utd"


def main():
    tmp = Path(tempfile.mkdtemp(prefix="hermes-verify-blog-", dir="/home/ubuntu/.hermes/cache/scratch"))
    try:
        (tmp / "posts").mkdir()
        for f in ("build.py", "style.css"):
            shutil.copy(HERE / f, tmp / f)
        for name, text in FIXTURES.items():
            (tmp / "posts" / name).write_text(text, encoding="utf-8")
        subprocess.run([sys.executable, "build.py"], cwd=tmp, check=True, capture_output=True)

        out = tmp / "docs"
        idx = (out / "index.html").read_text()
        body = idx.split("<body")[1].split(">", 1)[1]
        baru = (out / "2026-03-10-baru.html").read_text()
        lama = (out / "2026-01-05-lama.html").read_text()
        items = ET.parse(out / "feed.xml").getroot().findall("./channel/item")
        tag_pages = sorted(p.name for p in (out / "tag").glob("*.html"))

        checks = {
            "urutan: hero = terbaru": body.index('class="hero"') < body.index("2026-01-05-lama.html"),
            "hero pakai post terbaru": 'class="hero"' in idx and "Yang Baru" in idx.split('class="hero"')[1][:600],
            "kartu edisi sebelumnya": "2026-01-05-lama.html" in idx and "Edisi 01 ·" in idx,
            "label tanggal Indonesia": "10 Maret 2026" in idx and "5 Januari 2026" in idx,
            "warna tema ikut tag utama": f"--c:{THEME_BARU}" in idx and f"--c:{THEME_BARU}" in baru,
            "kutip frontmatter tidak bocor": "&quot;" not in body,
            "escaping HTML": "&lt;dengan &amp; tanda&gt;" in idx,
            "markdown": "<strong>lama</strong>" in lama and "<code>kode</code>" in lama,
            "list jadi <li>": "<li>satu</li>" in baru,
            "title halaman": "<title>Yang Baru —" in baru,
            "pager antar edisi": "Lebih lama" in baru and "Lebih baru" in lama,
            "halaman topik: 3 tag unik": tag_pages == ["ai.html", "man-utd.html", "saas.html"],
            "tag page memuat judul topik": "Man Utd" in (out / "tag" / "man-utd.html").read_text(),
            "rss urut + jumlah": len(items) == 2 and items[0].findtext("title") == "Yang Baru",
            ".nojekyll": (out / ".nojekyll").exists(),
            # --- v2: tema, css eksternal, dark/light ---
            "css eksternal tersalin": (out / "style.css").exists() and "/style.css" in idx,
            "css punya varian gelap": '[data-theme="dark"]' in (out / "style.css").read_text(),
            "tombol ganti tema ada": 'onclick="yabToggle()"' in idx and "yabToggle" in baru,
            "nama situs baru": "Yunar AI Brief" in idx and "Yunar AI Brief" in baru,
            "font sans (tanpa serif body)": "font-family:var(--sans)" in (out / "style.css").read_text(),
        }

        # --- v3: canonical, JSON-LD, sitemap, robots, llms.txt ---
        robots = (out / "robots.txt").read_text()
        llms = (out / "llms.txt").read_text()
        sm_root = ET.parse(out / "sitemap.xml").getroot()
        sm_locs = [e.text for e in sm_root.iter("{http://www.sitemaps.org/schemas/sitemap/0.9}loc")]
        ld_baru = ld_json(baru) or {}
        ld_idx = ld_json(idx) or {}
        checks.update({
            "canonical halaman edisi = URL dirinya": f'<link rel="canonical" href="{SITE}/2026-03-10-baru.html">' in baru,
            "canonical beranda": f'<link rel="canonical" href="{SITE}/">' in idx,
            "canonical halaman topik": f'<link rel="canonical" href="{SITE}/tag/man-utd.html">'
                                       in (out / "tag" / "man-utd.html").read_text(),
            "og:url ikut canonical": f'<meta property="og:url" content="{SITE}/2026-03-10-baru.html">' in baru,
            "og:type article vs website": 'content="article"' in baru and 'content="website"' in idx,
            "robots index,follow": 'name="robots" content="index,follow' in baru,
            "JSON-LD edisi = BlogPosting": ld_baru.get("@type") == "BlogPosting"
                                           and ld_baru.get("headline") == "Yang Baru"
                                           and ld_baru.get("datePublished") == "2026-03-10"
                                           and ld_baru.get("inLanguage") == "id",
            "JSON-LD edisi punya url + author": ld_baru.get("url") == f"{SITE}/2026-03-10-baru.html"
                                                 and ld_baru.get("author", {}).get("name"),
            "JSON-LD beranda = Blog + daftar edisi": ld_idx.get("@type") == "Blog"
                                                     and len(ld_idx.get("blogPost", [])) == 2,
            "sitemap: beranda + 2 edisi + 3 topik": len(sm_locs) == 6
                                                    and f"{SITE}/" in sm_locs
                                                    and f"{SITE}/2026-03-10-baru.html" in sm_locs
                                                    and f"{SITE}/tag/saas.html" in sm_locs,
            "sitemap pakai namespace resmi": sm_root.tag.endswith("urlset")
                                             and "sitemaps.org/schemas/sitemap" in sm_root.tag,
            "robots punya Sitemap + bot AI": "Sitemap: " + SITE + "/sitemap.xml" in robots
                                             and "User-agent: GPTBot" in robots
                                             and "User-agent: PerplexityBot" in robots
                                             and "User-agent: ClaudeBot" in robots,
            "robots tidak memblokir siapa pun": "Disallow: /" not in robots,
            "llms.txt format llmstxt.org": llms.startswith("# Yunar AI Brief\n") and "\n> " in llms,
            "llms.txt memuat kedua edisi + topik": "Yang Baru" in llms and "Yang Lama" in llms
                                                   and "## Topik" in llms and f"{SITE}/feed.xml" in llms,
        })
        # --- regresi: judul yang sudah memuat "Edisi" tidak digandakan di llms.txt ---
        sys.path.insert(0, str(tmp))
        import build as buildmod
        buildmod.OUT = tmp / "llms_probe"
        buildmod.OUT.mkdir()
        probe_item = {"slug": "probe", "date": date(2026, 1, 1), "tags": ["AI"],
                      "color": ("#000", "#000"),
                      "meta": {"title": "Edisi 07 — Judul Probe", "edisi": "07", "ringkas": "r"}}
        buildmod.write_llms([probe_item], {"AI": [probe_item]})
        probe_txt = (buildmod.OUT / "llms.txt").read_text()
        checks["llms.txt tidak menggandakan label edisi"] = (
            "Edisi 07 — Edisi 07" not in probe_txt and "[Edisi 07 — Judul Probe]" in probe_txt)

        # --- regresi kontras: semua warna tema harus lolos WCAG setelah digelapkan ---
        def _lum(hexc):
            h = hexc.lstrip("#")
            vals = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
            lin = [v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4 for v in vals]
            return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]

        def _ratio(a, b):
            la, lb = _lum(a), _lum(b)
            hi, lo = max(la, lb), min(la, lb)
            return (hi + 0.05) / (lo + 0.05)

        paper = "#fbfbfa"
        buruk = []
        for nama, (c, c2) in buildmod.THEMES.items():
            ink = buildmod.darken(c, 0.58)
            cta1, cta2 = buildmod.darken(c, 0.86), buildmod.darken(c2, 0.50)
            if _ratio(ink, paper) < 4.5:
                buruk.append(f"pil {nama}={_ratio(ink, paper):.2f}")
            if min(_ratio("#ffffff", cta1), _ratio("#ffffff", cta2)) < 4.5:
                buruk.append(f"cta {nama}={min(_ratio('#ffffff', cta1), _ratio('#ffffff', cta2)):.2f}")
        checks["kontras: semua warna tema >=4.5"] = not buruk
        if buruk:
            print("gagal kontras:", buruk)

        gagal = [k for k, ok in checks.items() if not ok]
        for k, ok in checks.items():
            print(("PASS  " if ok else "FAIL  ") + k)
        print(f"\n{len(checks) - len(gagal)}/{len(checks)} lolos")
        return 1 if gagal else 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
