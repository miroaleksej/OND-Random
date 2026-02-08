#!/usr/bin/env bash
set -euo pipefail

if [ $# -lt 1 ]; then
  echo "Usage: run_practrand.sh <input.bin> [RNG_test args...]"
  exit 2
fi

INPUT="$1"
shift
WORD="${PR_WORD:-64}"
EXTRA_ARGS="${PR_ARGS:-}"

if [ -n "${EXTRA_ARGS}" ]; then
  read -r -a EXTRA <<< "${EXTRA_ARGS}"
else
  EXTRA=()
fi

cat "${INPUT}" | RNG_test "stdin${WORD}" "${EXTRA[@]}" "$@"
