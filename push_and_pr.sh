#!/bin/bash

# push_and_pr.sh
# Usage: ./push_and_pr.sh "commit message"
# Commits, pushes, creates PR to main, enables auto-merge, and opens PR in browser.

set -e

if [ -z "$1" ]; then
  echo "Usage: $0 \"commit message\""
  exit 1
fi

# Check if user is authenticated with GitHub CLI
gh auth status &> /dev/null
if [ $? -ne 0 ]; then
  echo "[ERROR] You are not authenticated with GitHub CLI. Please run: gh auth login"
  exit 1
fi

COMMIT_MSG="$1"
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)

# Commit and push
git add .
git commit -m "$COMMIT_MSG"
git push origin "$CURRENT_BRANCH"

# Create PR (if not already exists)
PR_URL=$(gh pr view --json url -q ".url" 2>/dev/null || true)
if [ -z "$PR_URL" ]; then
  PR_URL=$(gh pr create --base main --head "$CURRENT_BRANCH" --title "$COMMIT_MSG" --body "$COMMIT_MSG" --web=false | grep -o 'https://github.com[^ ]*')
  echo "Pull request created: $PR_URL"
else
  echo "Pull request already exists: $PR_URL"
fi

# Enable auto-merge
gh pr merge --auto --squash

# Open PR in browser
if command -v open &> /dev/null; then
  open "$PR_URL"
elif command -v xdg-open &> /dev/null; then
  xdg-open "$PR_URL"
elif command -v start &> /dev/null; then
  start "$PR_URL"
else
  echo "Open the PR manually: $PR_URL"
fi

echo "PR created, auto-merge enabled, and PR opened in your browser."
echo "Wait for checks and merge to complete, then run the next script."