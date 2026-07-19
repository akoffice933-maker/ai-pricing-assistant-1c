.PHONY: help install test lint run backtest smoke-market zip \
        dashboard-install dashboard-dev dashboard-build dashboard-lint \
        docker-up docker-down clean

BACKEND_DIR := backend/ai_pricing_market_mvp
DASHBOARD_DIR := frontend/dashboard

help:
	@echo "Backend:"
	@echo "  make install           pip install -r requirements-dev.txt"
	@echo "  make test              pytest -q"
	@echo "  make lint              ruff check ."
	@echo "  make run               uvicorn main:app --reload --port 8000"
	@echo "  make backtest          прогнать backtest-харнесс на синтетическом примере"
	@echo "  make smoke-market      рассчитать индикаторы из docs/examples/raw_market_observations.csv"
	@echo ""
	@echo "Dashboard:"
	@echo "  make dashboard-install npm install"
	@echo "  make dashboard-dev     npm run dev"
	@echo "  make dashboard-build   npm run build"
	@echo "  make dashboard-lint    npm run lint"
	@echo ""
	@echo "Docker (весь стек):"
	@echo "  make docker-up         docker compose up --build"
	@echo "  make docker-down       docker compose down"
	@echo ""
	@echo "  make zip               собрать архив репозитория"
	@echo "  make clean             удалить __pycache__/dist/кэши"

install:
	cd $(BACKEND_DIR) && pip install -r requirements-dev.txt

test:
	cd $(BACKEND_DIR) && pytest -q

lint:
	cd $(BACKEND_DIR) && ruff check .

run:
	cd $(BACKEND_DIR) && uvicorn main:app --reload --port 8000

backtest:
	python scripts/backtest_elasticity.py $(BACKEND_DIR)/examples/backtest_sample.csv

smoke-market:
	python scripts/calculate_market_indicators.py \
		--input docs/examples/raw_market_observations.csv \
		--output docs/examples/calculated_market_indicators.json

dashboard-install:
	cd $(DASHBOARD_DIR) && npm install

dashboard-dev:
	cd $(DASHBOARD_DIR) && npm run dev

dashboard-build:
	cd $(DASHBOARD_DIR) && npm run build

dashboard-lint:
	cd $(DASHBOARD_DIR) && npm run lint

docker-up:
	docker compose up --build

docker-down:
	docker compose down

zip:
	cd .. && zip -qr ai-pricing-assistant-1c.zip ai-pricing-assistant-1c -x 'ai-pricing-assistant-1c/.git/*' '*/__pycache__/*' '*/node_modules/*'

clean:
	find . -type d -name "__pycache__" -not -path "*/node_modules/*" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name '*.pyc' -delete
	rm -rf $(BACKEND_DIR)/.pytest_cache $(BACKEND_DIR)/.ruff_cache
	rm -rf $(DASHBOARD_DIR)/dist
