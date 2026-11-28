#!/usr/bin/env bash
# Build + deploy ke Cloudflare Pages + tunggu benar-benar tersaji.
# Pakai: ./publish.sh "pesan commit"
#
# Sejak 28 Nov 2026 Kilas disajikan Cloudflare Pages (project: kilas), bukan GitHub Pages.
# git push tetap dilakukan sebagai arsip sumber, tapi BUKAN lagi jalur tayang.
set -euo pipefail
cd "$(dirname "$0")"

MSG="${1:-edisi baru $(date +%F)}"
PROJECT="kilas"
SITE="https://kilas.yunarprawira.com"

# Interpreter WAJIB eksplisit. `python3` di PATH mesin ini menunjuk venv agent-reach
# yang tidak punya paket `markdown`, sehingga build gagal dengan ModuleNotFoundError.
# Dulu ini tidak terlihat karena dulu `python3` menunjuk venv Hermes.
PY="/home/ubuntu/.hermes/hermes-agent/venv/bin/python"

"$PY" test_build.py
"$PY" build.py

# Cloudflare Pages memakai clean URL: /slug.html otomatis 308 -> /slug.
# CNAME sengaja DIBIARKAN: build.py menghasilkannya dan test_build.py memverifikasinya
# ("CNAME = host custom domain"). Di Cloudflare file itu tidak berpengaruh apa pun
# selain tersaji sebagai berkas teks biasa berisi nama host — bukan rahasia.
# Menghapusnya di sini hanya akan membuat test suite berbohong.

NEWEST=$(ls docs/*.html | grep -v '/index.html' | sort | tail -1 | xargs basename)
NEWEST_CLEAN="${NEWEST%.html}"

# Deploy dulu, commit belakangan: kalau deploy gagal, repo tidak mencatat edisi
# yang sebenarnya tidak pernah tayang.
export CLOUDFLARE_API_TOKEN="${CLOUDFLARE_API_TOKEN:-$(cat "$HOME/.hermes/secrets/cloudflare_token.txt")}"
npx --yes wrangler@4 pages deploy docs \
  --project-name="$PROJECT" --branch=main --commit-dirty=true 2>&1 | tail -5

git add -A
if git -c user.name="Yunar Prawira" \
      -c user.email="281810709+yunar-prawira@users.noreply.github.com" \
      commit -q -m "$MSG"; then
  git push -q origin main
  echo "pushed (arsip): $MSG"
fi
SHA=$(git rev-parse HEAD)

# Bukti tayang = halaman baru itu sendiri tersaji 200 di edge, bukan status build GitHub.
for i in $(seq 1 30); do
  page=$(curl -s -o /dev/null -w "%{http_code}" "$SITE/$NEWEST_CLEAN?cb=$SHA")
  css=$(curl -s -o /dev/null -w "%{http_code}" "$SITE/style.css?cb=$SHA")
  if [ "$page" = "200" ] && [ "$css" = "200" ]; then
    echo "LIVE ($SHA): $SITE/$NEWEST_CLEAN"
    exit 0
  fi
  sleep 4
done
echo "GAGAL: $NEWEST belum tersaji (page=$page css=$css)" >&2
exit 1
