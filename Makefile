# Makefile for Docker Compose project with a single service

# Variables
DOCKER_COMPOSE = docker compose
SERVICE_NAME = money-utils
ARGS := $(wordlist 3,$(words $(MAKECMDGOALS)),$(MAKECMDGOALS))

# Default target
.PHONY: help
help:
	@echo "Available commands:"
	@echo "  make build    - Build the Docker image"
	@echo "  make up       - Start the service"
	@echo "  make down     - Stop the service"
	@echo "  make restart  - Restart the service"
	@echo "  make logs     - View service logs"
	@echo "  make run      - Run only bash in container (will be removed afterwards)"
	@echo "  make shell    - Open a shell in the service container"
	@echo "  make clean    - Remove stopped containers and unused images"

# Build the Docker image
.PHONY: build
build:
	$(DOCKER_COMPOSE) build $(SERVICE_NAME)

# Start the service
.PHONY: up
up:
	$(DOCKER_COMPOSE) up -d $(SERVICE_NAME)

# Stop the service
.PHONY: down
down:
	$(DOCKER_COMPOSE) down

# Restart the service
.PHONY: restart
restart:
	$(DOCKER_COMPOSE) restart $(SERVICE_NAME)

# View service logs
.PHONY: logs
logs:
	$(DOCKER_COMPOSE) logs -f $(SERVICE_NAME)

# Run in the service container
.PHONY: run
run:
	$(DOCKER_COMPOSE) run --rm $(SERVICE_NAME) /bin/bash

# Open a shell in the service container
.PHONY: shell
shell:
	$(DOCKER_COMPOSE) exec $(SERVICE_NAME) /bin/sh

# Remove stopped containers and unused images
.PHONY: clean
clean:
	docker system prune -f

# All-in-one command to build, start, and view logs
.PHONY: all
all: build up logs

# Run tests
.PHONY: tasks
tasks:
	@echo "Running tests..."
	uv run pytask -xsv 2

# Run tests
.PHONY: tests
tests:
	@echo "Running tests..."
	uv run pytest -xsvv

.PHONY: runcrons
runcrons:
	uv run manage.py runcrons

