#!/usr/bin/env bash
set -euo pipefail
SRC_DB="${1:?source db path required}"
OUT_DIR="${2:-/tmp/cloudledger-dr}"
mkdir -p "${OUT_DIR}"
SNAP="${OUT_DIR}/snapshot.db"
ARCHIVE="${OUT_DIR}/cloudledger-backup.tar.gz"
python3 -c "import sqlite3; s=sqlite3.connect('${SRC_DB}'); d=sqlite3.connect('${SNAP}'); s.backup(d); s.close(); d.close()"
tar -czf "${ARCHIVE}" -C "${OUT_DIR}" snapshot.db
sha256sum "${ARCHIVE}" > "${ARCHIVE}.sha256"
echo "BACKUP_OK archive=${ARCHIVE} sha256=$(cut -d' ' -f1 ${ARCHIVE}.sha256)"
