.PHONY: run test benchmark seed clean

run:
	python start.py

test:
	python -m pytest backend/tests -v

benchmark:
	python scripts/benchmark.py --iterations 20 --device auto

seed:
	python scripts/seed_database.py
