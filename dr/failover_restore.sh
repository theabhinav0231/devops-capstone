#!/usr/bin/env bash
set -euo pipefail
ARCHIVE="${1:?archive path required}"
TARGET_DB="${2:?target db path required}"
T0=$(date +%s%3N)
sha256sum -c "${ARCHIVE}.sha256"
TMPD=$(mktemp -d)
tar -xzf "${ARCHIVE}" -C "${TMPD}"
cp "${TMPD}/snapshot.db" "${TARGET_DB}"
rm -rf "${TMPD}"
T1=$(date +%s%3N)
RTO=$((T1 - T0))
echo "RESTORE_OK target=${TARGET_DB} measured_rto_ms=${RTO}"
