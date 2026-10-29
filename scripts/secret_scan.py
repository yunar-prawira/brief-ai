#!/usr/bin/env python3
"""Pemindai rahasia sederhana untuk isi repo (dipakai pre-commit & `make scan`).

Pakai:
  python3 scripts/secret_scan.py            # scan semua file yang di-track git
  python3 scripts/secret_scan.py --staged   # scan hanya yang di-stage (pre-commit)

Exit code 1 kalau ada pola mencurigakan, 0 kalau bersih.
"""
import re
import subprocess
import sys

PATTERNS = [
    (r"gh[pousr]_[A-Za-z0-9]{20,}", "GitHub token"),
    (r"github_pat_[A-Za-z0-9_]{20,}", "GitHub fine-grained PAT"),
    (r"sk-[A-Za-z0-9]{20,}", "API key gaya OpenAI"),
    (r"AKIA[0-9A-Z]{16}", "AWS access key"),
    (r"AIza[0-9A-Za-z_\-]{30,}", "Google API key"),
    (r"-----BEGIN [A-Z ]*PRIVATE KEY", "private key"),
    (r"xox[baprs]-[A-Za-z0-9-]{10,}", "Slack token"),
    (r"eyJhbGciOi[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}", "JWT panjang"),
    (r"(?i)(service_role|supabase_service|db_password|api_key|apikey|secret_key|access_token)"
     r"\s*[:=]\s*['\"]?[A-Za-z0-9_\-\.]{12,}", "kredensial hardcoded"),
]

# yang memang boleh muncul (contoh di dokumentasi)
ALLOW = {
    "eyJhbGciOi",  # potongan dokumentasi JWT
}
SKIP_EXT = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".woff", ".woff2", ".pdf", ".mp4")


def files(staged: bool):
    if staged:
        out = subprocess.run(["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
                             capture_output=True, text=True, check=True).stdout
        return [f for f in out.splitlines() if f]
    out = subprocess.run(["git", "ls-files"], capture_output=True, text=True, check=True).stdout
    return [f for f in out.splitlines() if f]


def main():
    staged = "--staged" in sys.argv
    hits = []
    for path in files(staged):
        if path.lower().endswith(SKIP_EXT):
            continue
        try:
            text = open(path, encoding="utf-8", errors="ignore").read()
        except OSError:
            continue
        if path == "scripts/secret_scan.py":
            continue
        for i, line in enumerate(text.splitlines(), 1):
            for pat, label in PATTERNS:
                m = re.search(pat, line)
                if m and not any(a in m.group(0) for a in ALLOW):
                    hits.append((path, i, label, line.strip()[:100]))

    if hits:
        print("DITEMUKAN pola rahasia — commit dibatalkan:\n", file=sys.stderr)
        for p, i, label, snippet in hits:
            print(f"  {p}:{i}  [{label}]  {snippet}", file=sys.stderr)
        return 1
    print(f"bersih ({len(files(staged))} file diperiksa)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
