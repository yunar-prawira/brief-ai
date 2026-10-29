.PHONY: test build publish scan

test:    ## uji generator + skrip publish (wajib lulus sebelum publish)
	python3 test_build.py
	bash -n publish.sh
	@grep -q 'status" = "built"' publish.sh || { echo "FAIL  publish.sh: guard 'status = built' hilang" >&2; exit 1; }
	@echo "PASS  publish.sh: sintaks valid + tunggu status build 'built'"
	python3 scripts/secret_scan.py

scan:    ## cari pola rahasia di semua file yang di-track
	python3 scripts/secret_scan.py

build:
	python3 build.py

publish: ## build + commit + push + tunggu Pages live
	./publish.sh "$(m)"
