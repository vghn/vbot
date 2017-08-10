#!/usr/bin/env bash

# Bash strict mode
set -euo pipefail
IFS=$'\n\t'

# DEBUG
[ -z "${DEBUG:-}" ] || set -x

# VARs
APPDIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)/.."
GIT_BRANCH="${TRAVIS_BRANCH:-$(git symbolic-ref --short HEAD)}"

# Detect stage
if [[ "${TRAVIS_PULL_REQUEST:-false}" == 'false' ]]; then
  if [[ "$GIT_BRANCH" == 'master' ]]; then
    STAGE='prod'
  elif [[ "$GIT_BRANCH" == 'dev' ]]; then
    STAGE='dev'
  fi
fi

if [ -z ${STAGE+x} ]; then
  echo "Not deploying changes from ${GIT_BRANCH} (only master/dev)"
else
  # Decrypt .env file
  if [[ ! -s "${APPDIR}/.env" ]]; then
    ( echo "$ENCRYPT_KEY" | base64 --decode ) | \
      gpg --decrypt --passphrase-fd 0 --batch --output "${APPDIR}/.env" \
      "${APPDIR}/.env.gpg"
  fi

  # Load environment
  # shellcheck disable=1090
  . "${APPDIR}/.env" 2>/dev/null || true

  # Deploy
  echo "Deploying stage from branch '${GIT_BRANCH}' to '${STAGE}'"
  npm install -g
  serverless deploy --stage "$STAGE"
fi
