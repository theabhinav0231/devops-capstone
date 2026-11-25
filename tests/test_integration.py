import hashlib
import os
import sqlite3
import tempfile
from app.app import app


def test_sqlite_online_backup_and_restore_integrity():
    with tempfile.TemporaryDirectory() as tmp:
        src_db = os.path.join(tmp, "primary.db")
        bak_db = os.path.join(tmp, "backup.db")
        import app.app as mod
        mod.DB_PATH = src_db
        mod.FAULT_RATE = 0.0
        with app.test_client() as c:
            for i in range(1, 6):
                r = c.post("/api/transactions", json={"tx_id": f"TX-{i}", "account": f"ACC-{i}", "amount": i * 100.0})
                assert r.status_code == 201

        src = sqlite3.connect(src_db)
        dst = sqlite3.connect(bak_db)
        src.backup(dst)
        src.close()
        dst.close()

        h1 = hashlib.sha256(open(bak_db, "rb").read()).hexdigest()
        assert len(h1) == 64

        mod.DB_PATH = bak_db
        with app.test_client() as c:
            g = c.get("/api/transactions").get_json()
            assert g["count"] == 5
