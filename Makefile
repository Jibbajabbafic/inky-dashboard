RPI_HOST ?= inky
RPI_USER ?= inky
REMOTE_DIR ?= /home/$(RPI_USER)/src/inky-dashboard

.PHONY: setup setup-deploy run deploy deploy-env deploy-restart deploy-status deploy-logs

setup:
	uv sync

run:
	uv run main.py

deploy:
	./scripts/deploy.sh

deploy-env:
	rsync -avz .env "$(RPI_HOST):$(REMOTE_DIR)/.env"
	ssh -t "$(RPI_HOST)" "sudo systemctl restart inky-dashboard && systemctl is-active inky-dashboard"

deploy-restart:
	ssh -t "$(RPI_HOST)" "sudo systemctl restart inky-dashboard && systemctl is-active inky-dashboard"

deploy-status:
	ssh -t "$(RPI_HOST)" "systemctl --no-pager status inky-dashboard"

deploy-logs:
	ssh -t "$(RPI_HOST)" "journalctl -u inky-dashboard -n 50 --no-pager"
