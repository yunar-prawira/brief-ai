#!/usr/bin/env bash
# Build + push + tunggu GitHub Pages live.
# Pakai: ./publish.sh "pesan commit"
set -euo pipefail
cd "$(dirname "$0")"

MSG="${1:-edisi baru $(date +%F)}"
SITE="https://yunar-prawira.github.io/brief-ai"

python3 test_build.py
python3 build.py

git add -A
if git -c user.name="Yunar Prawira" \
      -c user.email="281810709+yunarganteng@users.noreply.github.com" \
      commit -q -m "$MSG"; then
  git push -q origin main
  echo "pushed: $MSG"
else
  echo "tidak ada perubahan untuk di-commit"
fi

# file post terbaru yang harus bisa diakses di internet
NEWEST=$(ls -t docs/*.html | grep -v '/index.html' | head -1 | xargs basename)
for i in $(seq 1 30); do
  code=$(curl -s -o /dev/null -w "%{http_code}" "$SITE/$NEWEST")
  if [ "$code" = "200" ]; then
    echo "LIVE: $SITE/$NEWEST"
    exit 0
  fi
  sleep 6
done
echo "GAGAL: $NEWEST belum 200 setelah ~3 menit" >&2
exit 1
