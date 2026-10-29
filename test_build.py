#!/usr/bin/env python3
"""Uji build.py: python3 test_build.py"""
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent

FIXTURES = {
    "2026-01-05-lama.md": '---\ntitle: "Yang Lama"\ndate: 2026-01-05\nedisi: "01"\ntag: "AI"\n'
                          'ringkas: "post lama"\n---\nIsi **lama** dengan `kode`.\n',
    "2026-03-10-baru.md": '---\ntitle: "Yang Baru"\ndate: 2026-03-10\nedisi: "02"\ntag: "Man Utd, SaaS"\n'
                          'ringkas: "post baru <dengan & tanda>"\n---\n- satu\n- dua\n',
}


def main():
    tmp = Path(tempfile.mkdtemp(prefix="hermes-verify-blog-", dir="/home/ubuntu/.hermes/cache/scratch"))
    try:
        (tmp / "posts").mkdir()
        shutil.copy(HERE / "build.py", tmp / "build.py")
        for name, text in FIXTURES.items():
            (tmp / "posts" / name).write_text(text, encoding="utf-8")
        subprocess.run([sys.executable, "build.py"], cwd=tmp, check=True, capture_output=True)

        out = tmp / "docs"
        idx = (out / "index.html").read_text()
        body = idx.split("<body")[1].split(">", 1)[1]
        baru = (out / "2026-03-10-baru.html").read_text()
        lama = (out / "2026-01-05-lama.html").read_text()
        items = ET.parse(out / "feed.xml").getroot().findall("./channel/item")
        theme_baru = "#d92b2b"  # tag pertama "Man Utd"
        tag_pages = sorted(p.name for p in (out / "tag").glob("*.html"))

        checks = {
            "urutan: hero = terbaru": idx.index("Edisi terbaru") < idx.index("2026-01-05-lama.html"),
            "hero pakai post terbaru": 'class="hero"' in idx and "Yang Baru" in idx.split('class="hero"')[1][:600],
            "kartu edisi sebelumnya": "2026-01-05-lama.html" in idx and "Edisi 01 ·" in idx,
            "label tanggal Indonesia": "10 Maret 2026" in idx and "5 Januari 2026" in idx,
            "warna tema ikut tag utama": f"--c:{theme_baru}" in idx and f"--c:{theme_baru}" in baru,
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
        }
        gagal = [k for k, ok in checks.items() if not ok]
        for k, ok in checks.items():
            print(("PASS  " if ok else "FAIL  ") + k)
        print(f"\n{len(checks) - len(gagal)}/{len(checks)} lolos")
        return 1 if gagal else 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
