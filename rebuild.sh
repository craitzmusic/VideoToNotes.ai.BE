#!/bin/zsh (23/06/2025)

echo "🛑 Stopping and removing containers..."
docker compose down

echo "🔄 Rebuilding and starting containers..."
docker compose up --build