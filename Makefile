test:
	uv run main.py

deploy:
	./scripts/deploy.sh

run:
	./scripts/deploy.sh
	ssh -t inky "cd /home/inky/src/inky-dashboard && ~/.local/bin/uv run main.py"

setup:
	uv sync
	uv run playwright install chromium
	uv run playwright install-deps chromium
