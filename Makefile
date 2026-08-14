.PHONY: install run test screenshots clean
install:
	python3 -m pip install -e '.[dev]'
run:
	python3 -m uvicorn app.main:app --reload
test:
	python3 -m pytest
screenshots:
	bash scripts/capture_screenshots.sh
clean:
	rm -rf .pytest_cache data/cloudatlas.db

