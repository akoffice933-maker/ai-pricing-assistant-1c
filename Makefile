.PHONY: help run-backend test-backend smoke-market zip clean

help:
	@echo "Targets:"
	@echo "  run-backend   Run FastAPI backend on port 8000"
	@echo "  test-backend  Run backend smoke tests"
	@echo "  smoke-market  Calculate market indicators from sample raw CSV"
	@echo "  zip           Build repository archive"
	@echo "  clean         Remove caches"

run-backend:
	cd backend/ai_pricing_market_mvp && uvicorn main:app --reload --port 8000

test-backend:
	cd backend/ai_pricing_market_mvp && python -m py_compile main.py && pytest tests_smoke.py

smoke-market:
	python scripts/calculate_market_indicators.py \
		--input docs/examples/raw_market_observations.csv \
		--output docs/examples/calculated_market_indicators.json

zip:
	cd .. && zip -qr ai-pricing-assistant-1c.zip ai-pricing-assistant-1c -x 'ai-pricing-assistant-1c/.git/*' '*/__pycache__/*'

clean:
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	find . -type f -name '*.pyc' -delete
