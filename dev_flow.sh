#!/bin/bash

# dev_flow.sh
# Usage: ./dev_flow.sh "commit message" [new-branch-name]
# Full dev automation: commit, push, PR, auto-merge, wait for merge, create new branch.
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
  echo -e "${STEP} ${BLUE}$1${NC}"
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

if [ -z "$1" ]; then
  log_error "Usage: $0 \"commit message\" [new-branch-name]"
  exit 1
fi

COMMIT_MSG="$1"
NEW_BRANCH="$2"
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)

# Check GitHub CLI authentication
log_step "Checking GitHub CLI authentication..."
if ! gh auth status &> /dev/null; then
  log_error "You are not authenticated with GitHub CLI. Please run: gh auth login"
  exit 1
fi
log_done 0

# Commit and push
log_step "Committing and pushing changes..."
t0=$(timer_start)
git add .
git commit -m "$COMMIT_MSG"
git push origin "$CURRENT_BRANCH"
log_done $(timer_end $t0)

# Create PR (if not already exists)
log_step "Creating pull request (if needed)..."
t0=$(timer_start)
PR_URL=$(gh pr view --json url -q ".url" 2>/dev/null || true)
if [ -z "$PR_URL" ]; then
  PR_URL=$(gh pr create --base main --head "$CURRENT_BRANCH" --title "$COMMIT_MSG" --body "$COMMIT_MSG" --web=false | grep -o 'https://github.com[^ ]*')
  echo -e "   ${CHECK} Pull request created: ${PR_URL}"
else
  echo -e "   ${CHECK} Pull request already exists: ${PR_URL}"
fi
log_done $(timer_end $t0)

# Enable auto-merge
log_step "Enabling auto-merge for PR..."
t0=$(timer_start)
gh pr merge --auto --squash
log_done $(timer_end $t0)

# Open PR in Google Chrome (macOS) or default browser elsewhere
log_step "Opening PR in Google Chrome..."
if [[ "$OSTYPE" == "darwin"* ]]; then
  open -a "Google Chrome" "$PR_URL"
elif command -v xdg-open &> /dev/null; then
  xdg-open "$PR_URL"
elif command -v start &> /dev/null; then
  start "$PR_URL"
else
  echo "   Open the PR manually: $PR_URL"
fi
log_done 0

# Wait for PR to be merged
log_step "Waiting for PR to be merged (auto-merge enabled)..."
t0=$(timer_start)
PR_NUMBER=$(gh pr list --head "$CURRENT_BRANCH" --json number -q '.[0].number' 2>/dev/null || true)
if [ -z "$PR_NUMBER" ]; then
  log_error "No PR found for branch $CURRENT_BRANCH."
  exit 1
fi
while true; do
  PR_STATE=$(gh pr view "$PR_NUMBER" --json state -q ".state")
  if [ "$PR_STATE" = "MERGED" ]; then
    echo -e "   ${CHECK} PR #$PR_NUMBER has been merged!"
    # Play a beep sound and show a highlighted message
    echo -e "\a"
    echo -e "${YELLOW}🔔 Merge complete! You can close the PR tab in Chrome. 🔔${NC}"
    break
  fi
  echo -e "   ${WAIT} Waiting... (current state: $PR_STATE)"
  sleep 10
done
log_done $(timer_end $t0)

# Checkout main and pull
log_step "Checking out main and pulling latest changes..."
t0=$(timer_start)
git checkout main
git pull
log_done $(timer_end $t0)

# Determine new branch name
if [ -n "$NEW_BRANCH" ]; then
  FINAL_BRANCH="$NEW_BRANCH"
else
  if [[ "$CURRENT_BRANCH" =~ (.+)-v([0-9]+)$ ]]; then
    BASE_NAME="${BASH_REMATCH[1]}"
    VERSION="${BASH_REMATCH[2]}"
    NEW_VERSION=$((VERSION + 1))
    FINAL_BRANCH="${BASE_NAME}-v${NEW_VERSION}"
  else
    BASE_NAME="$CURRENT_BRANCH"
    FINAL_BRANCH="${BASE_NAME}-v2"
  fi
fi

# Create and switch to new branch
log_step "Creating and switching to new branch: $FINAL_BRANCH"
t0=$(timer_start)
git checkout -b "$FINAL_BRANCH"
log_done $(timer_end $t0)

echo -e "${GREEN}🎉 All done! You are now on branch: ${FINAL_BRANCH}${NC}" 