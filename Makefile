.PHONY: test test-ui build publish scan

PY ?= python3
VPY = /home/ubuntu/.hermes/hermes-agent/venv/bin/python

test:    ## uji generator + skrip publish (wajib lulus sebelum publish)
	$(PY) test_build.py
	bash -n publish.sh
	@grep -q 'status" = "built"' publish.sh || { echo "FAIL  publish.sh: guard 'status = built' hilang" >&2; exit 1; }
	@echo "PASS  publish.sh: sintaks valid + tunggu status build 'built'"
	$(PY) scripts/secret_scan.py

test-ui: ## uji fungsional di browser sungguhan (butuh playwright di venv Hermes)
	$(VPY) scripts/test_ui.py

scan:    ## cari pola rahasia di semua file yang di-track
	python3 scripts/secret_scan.py

build:
	python3 build.py

publish: ## build + commit + push + tunggu Pages live
	./publish.sh "$(m)"
