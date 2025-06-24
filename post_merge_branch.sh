#!/bin/bash

# post_merge_branch.sh
# Usage: ./post_merge_branch.sh [new-branch-name]
# Waits for PR merge, checks out main, pulls, creates new branch (named or versioned).

set -e

CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)

# Get PR number for current branch (merged or open)
PR_NUMBER=$(gh pr list --head "$CURRENT_BRANCH" --state merged --json number -q '.[0].number' 2>/dev/null || true)
if [ -z "$PR_NUMBER" ]; then
  PR_NUMBER=$(gh pr list --head "$CURRENT_BRANCH" --state open --json number -q '.[0].number' 2>/dev/null || true)
fi

if [ -z "$PR_NUMBER" ]; then
  echo "No PR found for branch $CURRENT_BRANCH. Please ensure the PR was created and merged."
  exit 1
fi

# Wait for PR to be merged
while true; do
  PR_STATE=$(gh pr view "$PR_NUMBER" --json state -q ".state")
  if [ "$PR_STATE" = "MERGED" ]; then
    echo "PR #$PR_NUMBER has been merged!"
    break
  fi
  echo "Waiting for PR #$PR_NUMBER to be merged... (current state: $PR_STATE)"
  sleep 10
done

# Checkout main and pull
git checkout main
git pull

# Determine new branch name
if [ -n "$1" ]; then
  NEW_BRANCH="$1"
else
  if [[ "$CURRENT_BRANCH" =~ (.+)-v([0-9]+)$ ]]; then
    BASE_NAME="${BASH_REMATCH[1]}"
    VERSION="${BASH_REMATCH[2]}"
    NEW_VERSION=$((VERSION + 1))
    NEW_BRANCH="${BASE_NAME}-v${NEW_VERSION}"
  else
    BASE_NAME="$CURRENT_BRANCH"
    NEW_BRANCH="${BASE_NAME}-v2"
  fi
fi

# Create and switch to new branch
git checkout -b "$NEW_BRANCH"
echo "Created and switched to new branch: $NEW_BRANCH"