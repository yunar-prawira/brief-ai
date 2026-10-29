#!/usr/bin/env bash
# Build + push + tunggu GitHub Pages benar-benar men-deploy commit terakhir.
# Pakai: ./publish.sh "pesan commit"
set -euo pipefail
cd "$(dirname "$0")"

MSG="${1:-edisi baru $(date +%F)}"
REPO="yunar-prawira/brief-ai"
SITE="https://yunar-prawira.github.io/brief-ai"

python3 test_build.py
python3 build.py

git add -A
if git -c user.name="Yunar Prawira" \
      -c user.email="281810709+yunarganteng@users.noreply.github.com" \
      commit -q -m "$MSG"; then
  git push -q origin main
  echo "pushed: $MSG"
fi
SHA=$(git rev-parse HEAD)
NEWEST=$(ls docs/*.html | grep -v '/index.html' | sort | tail -1 | xargs basename)

# tunggu build Pages untuk commit ini selesai, lalu pastikan halaman + css benar-benar tersaji
for i in $(seq 1 40); do
  built=$(gh api "repos/$REPO/pages/builds/latest" --jq '.commit' 2>/dev/null || true)
  page=$(curl -s -o /dev/null -w "%{http_code}" "$SITE/$NEWEST")
  css=$(curl -s -o /dev/null -w "%{http_code}" "$SITE/style.css")
  if [ "$built" = "$SHA" ] && [ "$page" = "200" ] && [ "$css" = "200" ]; then
    echo "LIVE ($SHA): $SITE/$NEWEST"
    exit 0
  fi
  sleep 6
done
echo "GAGAL: build $SHA belum tersaji (page=$page css=$css built=$built)" >&2
exit 1
