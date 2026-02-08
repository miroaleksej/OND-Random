#!/usr/bin/env bash
set -euo pipefail

if [ $# -lt 2 ]; then
  echo "Usage: run_testu01.sh <battery> <input.bin>"
  exit 2
fi

BATTERY="$1"
INPUT="$2"

exec /usr/local/bin/testu01_file_runner "${BATTERY}" "${INPUT}"
