.PHONY: help install analyze clean test

help:
	@echo "CannaPeace HVAC Analytics - Make Targets"
	@echo ""
	@echo "  make install    Install Python dependencies"
	@echo "  make analyze    Run full pipeline (ingestion → EDA → recharge → anomaly)"
	@echo "  make clean      Remove generated data (keeps raw/)"
	@echo "  make test       Run tests"
	@echo ""
	@echo "Quick start:"
	@echo "  1. Drop FBox CSV exports into inbox/"
	@echo "  2. make install"
	@echo "  3. make analyze"
	@echo "  4. View reports/ folder"

install:
	@echo "📦 Installing dependencies..."
	pip install -r requirements.txt
	@echo "✅ Installation complete"

analyze:
	@echo "🚀 Running HVAC analytics pipeline..."
	@echo ""
	@echo "Phase 1: Ingestion (CSV → Parquet)"
	python src/pipeline.py --phase ingestion
	@echo ""
	@echo "Phase 2: EDA & Characterization"
	python src/pipeline.py --phase eda
	@echo ""
	@echo "Phase 3: Recharge Verdict"
	python src/pipeline.py --phase recharge
	@echo ""
	@echo "Phase 4: Anomaly Detection"
	python src/pipeline.py --phase anomaly
	@echo ""
	@echo "✅ Pipeline complete! Check reports/ folder"

clean:
	@echo "🧹 Cleaning generated data..."
	rm -rf data/aligned/* data/views/* data/db/* reports/*
	@echo "⚠️  Keeping raw data in data/raw/"
	@echo "✅ Clean complete"

test:
	@echo "🧪 Running tests..."
	pytest tests/ -v
