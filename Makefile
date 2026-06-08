deploy:
	./scripts/deploy.sh

run:
	./scripts/deploy.sh
	ssh -t inky "cd /home/inky/src/inky-dashboard && ~/.local/bin/uv run main.py"
