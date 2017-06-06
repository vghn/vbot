#!/usr/bin/env bash

# Bash strict mode
set -euo pipefail
IFS=$'\n\t'

# DEBUG
[ -z "${DEBUG:-}" ] || set -x

# Get Git branch
GIT_BRANCH="${TRAVIS_BRANCH:-$(git symbolic-ref --short HEAD)}"

# Load private environment
# shellcheck disable=1090
. "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)/../.env" 2>/dev/null || true

echo 'Detect stage'
if [[ "${TRAVIS_PULL_REQUEST:-false}" == 'false' ]]; then
  if [[ "$GIT_BRANCH" == 'master' ]]; then
    STAGE='prod'
  elif [[ "$GIT_BRANCH" == 'dev' ]]; then
    STAGE='dev'
  fi
fi

if [ -z ${STAGE+x} ]; then
  echo 'Not deploying changes'
else
  echo "Deploying stage from branch '${GIT_BRANCH}' to '${STAGE}'"
  npm install
  serverless deploy --stage "$STAGE"
fi