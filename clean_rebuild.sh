#!/bin/bash

# clean_rebuild.sh
# Fully cleans, rebuilds, and starts Docker Compose services for the backend.
# Shows colored logs, icons, and timing for each step.

set -e

# Color and icon helpers
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[1;34m'
RED='\033[0;31m'
CYAN='\033[1;36m'
NC='\033[0m' # No Color
CHECK="${GREEN}✔${NC}"
CROSS="${RED}✖${NC}"
WAIT="${YELLOW}⏳${NC}"
STEP="${CYAN}➤${NC}"

function log_step() {
  echo -e "\n${STEP} ${BLUE}$1${NC}"
}

function log_done() {
  local duration=$1
  echo -e "   ${CHECK} Done (${duration}s)"
}

function log_error() {
  echo -e "${CROSS} ${RED}$1${NC}"
}

function timer_start() {
  date +%s
}

function timer_end() {
  local start=$1
  local end=$(date +%s)
  echo $((end - start))
}

log_step "Bringing down existing Docker services..."
t0=$(timer_start)
docker compose down
log_done $(timer_end $t0)

log_step "Building Docker images without cache..."
t0=$(timer_start)
docker compose build --no-cache
log_done $(timer_end $t0)

log_step "Starting Docker services..."
t0=$(timer_start)
docker compose up
log_done $(timer_end $t0)

echo -e "\n${GREEN}🎉 Docker clean rebuild and startup complete!${NC}" 