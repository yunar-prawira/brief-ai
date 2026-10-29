.PHONY: test build publish

test:    ## uji generator (wajib lulus sebelum publish)
	python3 test_build.py

build:
	python3 build.py

publish: ## build + commit + push + tunggu Pages live
	./publish.sh "$(m)"
