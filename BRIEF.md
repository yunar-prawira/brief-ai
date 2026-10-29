# Yunar AI Brief — panduan produksi

Blog statis pribadi Yunar. Audiens utama: Yunar sendiri. Tujuannya: dia selesai baca
dalam ~5 menit dan merasa lebih tahu daripada tadi.

- Situs: https://yunar-prawira.github.io/brief-ai/
- Repo: https://github.com/yunar-prawira/brief-ai (public, GitHub Pages dari `main` / `docs`)

## Struktur

```
build.py        generator statis (markdown -> HTML + RSS)
style.css       tema (semua sans, aksen warna per topik, gelap/terang)
posts/*.md      sumber tulisan (ini yang diedit)
docs/           hasil build (di-commit, disajikan GitHub Pages)
publish.sh      build + test + commit + push + tunggu deploy
test_build.py   uji build (jalankan sebelum publish)
log/seen.json   daftar URL yang sudah pernah dipakai (anti-ulang)
```

## Menulis edisi baru

1. Nama file: `posts/YYYY-MM-DD-edisi-NN.md` (tanggal WIB, NN dua digit, urut naik).
2. Frontmatter:

```
---
title: "Edisi 03 — judul yang spesifik, bukan clickbait"
date: 2026-10-30
edisi: "03"
tag: "AI, HR"
ringkas: "Satu paragraf, maksimal ~240 karakter, jadi ini yang muncul di kartu & RSS."
---
```

`tag` boleh lebih dari satu, yang pertama menentukan warna. Tag yang punya warna khusus:
`AI`, `Dev`, `Man Utd`, `HR`, `SaaS`, `Product`, `Indonesia`, `Politik`, `Riset`.
Tag lain tetap jalan pakai warna default.

3. Isi: 600–1000 kata, Bahasa Indonesia, sudut pandang "aku" (Rina) ke "kamu" (Yunar).
   Setiap klaim angka wajib ada tautan sumbernya. Akhiri dengan satu bagian
   "kenapa ini penting buatmu" atau "benang merahnya".

## Publish

```bash
cd ~/ai-brief && ./publish.sh "edisi 03 — <judul>"
```

Skrip ini: jalankan tes, build, commit, push, lalu tunggu sampai GitHub Pages
benar-benar menyajikan commit tersebut, dan mencetak URL `LIVE`. Kalau keluar
`GAGAL`, build Pages belum selesai — jangan mengklaim sudah tayang.

## Aturan isi

- Jangan mengarang fakta, angka, kutipan, atau tanggal. Sumber tipis = edisi lebih pendek.
- **Inti tiap edisi adalah AI itu sendiri**: berita AI, perkembangan model/riset/tool, dan AI
  untuk development. Minimal 3 item inti, dan bagian terbesar edisi harus tentang ini.
- **Topik minat itu opsional, 0-2 item per edisi.** Manchester United, HR/payroll, SaaS &
  pricing, product build, Indonesia, politik: hanya masuk kalau hari itu ada berita nyata,
  dan selalu lewat kacamata AI — AI untuk data/scouting bola, AI di rekrutmen & payroll,
  AI dalam pricing/produk SaaS, agentic coding & tools build, kebijakan/adopsi AI di
  Indonesia, politik regulasi AI. Berita cedera pemain, jadwal klub, startup tanpa AI, atau
  politik umum tanpa AI = tidak masuk.
- **Tidak wajib ada item topik minat.** Kalau tidak ada sudut AI yang nyata, lewati dan
  terbitkan edisi yang murni AI. Jangan memaksakan topik supaya edisi terlihat lebar.
- Hindari cerita yang sudah dipakai: cek `log/seen.json` dan 3 post terakhir.
- Tanpa buzzword ("revolusioner", "game changer"). Angka > adjektiva.

## Kalau tampilan diubah

- Semua CSS ada di `style.css` (bukan di build.py). Varian gelap memakai
  `:root[data-theme="dark"]` + `prefers-color-scheme`.
- Warna topik diatur di dict `THEMES` pada `build.py` sebagai pasangan (warna, warna gradien).
- Setelah mengubah, wajib: `python3 test_build.py` lalu `./publish.sh "..."`.
