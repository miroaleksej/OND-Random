#!/usr/bin/env bash
set -euo pipefail

if [ $# -lt 1 ]; then
  echo "Usage: run_nist_sts.sh <input.bin>"
  exit 2
fi

INPUT="$1"
ASSESS="${STS_ASSESS:-/opt/nist-sts/assess}"
WORKDIR="${STS_WORKDIR:-/tmp/nist-sts}"

if [ ! -x "${ASSESS}" ]; then
  echo "NIST STS assess binary not found at ${ASSESS}"
  echo "Mount your STS build at /opt/nist-sts or set STS_ASSESS"
  exit 3
fi

mkdir -p "${WORKDIR}"
cd "${WORKDIR}"

if [ -n "${STS_CONFIG:-}" ]; then
  "${ASSESS}" < "${STS_CONFIG}"
else
  printf "1\n0\n0\n0\n0\n%s\n1\n0\n" "${INPUT}" | "${ASSESS}"
fi
