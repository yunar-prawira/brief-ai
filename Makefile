.PHONY: test build publish

test:    ## uji generator + skrip publish (wajib lulus sebelum publish)
	python3 test_build.py
	bash -n publish.sh
	@grep -q 'status" = "built"' publish.sh || { echo "FAIL  publish.sh: guard 'status = built' hilang" >&2; exit 1; }
	@echo "PASS  publish.sh: sintaks valid + tunggu status build 'built'"

build:
	python3 build.py

publish: ## build + commit + push + tunggu Pages live
	./publish.sh "$(m)"
