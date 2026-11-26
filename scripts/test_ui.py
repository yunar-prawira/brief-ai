#!/usr/bin/env python3
"""Uji FUNGSIONAL halaman brief-ai di browser sungguhan (Playwright).

Menjalankan server statis sendiri, lalu membuktikan halaman benar-benar bekerja:
hero memuat edisi terbaru, arsip tampil, tombol tema mengganti tema, klik kartu
membuka edisi yang benar, canonical menunjuk URL produksi, topik render, dan
tidak ada error console. Menyimpan screenshot sebagai bukti visual.

Jalankan:  make test-ui      (memakai python venv Hermes yang punya playwright)
       atau python3 scripts/test_ui.py   (kalau playwright ada di python itu)
"""
import glob
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
PROD = "https://kilas.yunarprawira.com"
SHOT_DIR = ROOT / "log" / "ui-proof"

try:
    from playwright.sync_api import sync_playwright
except ImportError:  # pesan jelas, jangan traceback mentah
    sys.exit("playwright belum ada di python ini. Jalankan: make test-ui "
             "(memakai venv Hermes) atau pip install playwright && playwright install chromium")


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def wait_port(port: int, timeout: float = 15.0) -> bool:
    end = time.time() + timeout
    while time.time() < end:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=1):
                return True
        except OSError:
            time.sleep(0.15)
    return False


def chrome_executable():
    """Pakai build chromium yang sudah ada di cache bila versinya beda dari library."""
    cands = sorted(glob.glob(os.path.expanduser(
        "~/.cache/ms-playwright/chromium-*/chrome-linux64/chrome")))
    return cands[-1] if cands else None


def run_checks(base: str):
    checks = {}
    console_errors = []
    SHOT_DIR.mkdir(parents=True, exist_ok=True)
    shot_home = SHOT_DIR / "home.png"
    shot_post = SHOT_DIR / "edisi-terbaru.png"

    with sync_playwright() as p:
        launch_kw = {"executable_path": chrome_executable()} if chrome_executable() else {}
        browser = p.chromium.launch(**launch_kw)
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        page.on("console", lambda m: console_errors.append(m.text) if m.type == "error" else None)
        page.on("pageerror", lambda e: console_errors.append(str(e)))

        page.goto(base + "/", wait_until="networkidle")
        checks["judul dokumen"] = page.title() == "Yunar AI Brief"
        hero = page.inner_text("section.hero h1")
        checks["hero memuat edisi terbaru"] = "Edisi" in hero
        cards = page.locator("a.card")
        checks["arsip tampil"] = cards.count() >= 1
        checks["canonical beranda = URL produksi"] = (
            page.get_attribute('link[rel="canonical"]', "href") == PROD + "/")
        checks["rail topik ada"] = page.locator("div.rail a").count() >= 3

        before = page.evaluate("document.documentElement.dataset.theme || ''")
        page.click("button.tg")
        after = page.evaluate("document.documentElement.dataset.theme || ''")
        page.click("button.tg")
        back = page.evaluate("document.documentElement.dataset.theme || ''")
        checks["toggle tema mengganti tema"] = after != before and after in ("dark", "light")
        checks["toggle tema bisa dibalik"] = back != after and back in ("dark", "light")
        page.screenshot(path=str(shot_home))

        href = cards.first.get_attribute("href")
        cards.first.click()
        page.wait_for_load_state("networkidle")
        checks["klik kartu membuka edisi"] = page.url == href
        checks["h1 edisi cocok dengan judul dokumen"] = page.inner_text("h1").strip() in page.title()
        checks["canonical edisi = URL dirinya"] = (
            page.get_attribute('link[rel="canonical"]', "href") == href)
        checks["artikel punya lede + isi"] = (page.locator("p.lede").count() == 1
                                              and page.locator("div.body p").count() >= 3)
        checks["artikel menautkan sumber"] = page.locator("div.body a").count() >= 1
        page.screenshot(path=str(shot_post))

        page.goto(base + "/", wait_until="networkidle")
        rail = page.locator("div.rail a")
        tag_link = rail.first.get_attribute("href") if rail.count() else None
        checks["rail topik punya tautan"] = bool(tag_link)
        if tag_link:
            page.goto(tag_link, wait_until="networkidle")
            tag_hero = page.inner_text("section.hero").upper()
            checks["halaman topik render"] = "TOPIK" in tag_hero and "TULISAN" in tag_hero
            checks["halaman topik berisi kartu"] = page.locator("a.card").count() >= 1

        checks["tanpa error console"] = not console_errors
        if console_errors:
            print("console errors:", console_errors[:3], file=sys.stderr)
        browser.close()

    return checks, [shot_home, shot_post]


def main():
    if not (DOCS / "index.html").exists():
        sys.exit("docs/index.html belum ada — jalankan: python3 build.py")
    port = free_port()
    server = subprocess.Popen([sys.executable, "-m", "http.server", str(port), "--bind", "127.0.0.1"],
                              cwd=str(DOCS), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        if not wait_port(port):
            sys.exit(f"server statis gagal siap di port {port}")
        checks, shots = run_checks(f"http://127.0.0.1:{port}")
    finally:
        server.terminate()
        try:
            server.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server.kill()

    gagal = [k for k, ok in checks.items() if not ok]
    for k, ok in checks.items():
        print(("PASS  " if ok else "FAIL  ") + k)
    print(f"\n{len(checks) - len(gagal)}/{len(checks)} lolos")
    for s in shots:
        print(f"screenshot: {s}")
    return 1 if gagal else 0


if __name__ == "__main__":
    sys.exit(main())
