#!/usr/bin/env python3
"""CloudLedger - FinTech Payment & Transaction Ledger Microservice (ENSP461 Capstone - Abhinav Kumar)."""
import hashlib
import hmac
import json
import os
import random
import sqlite3
import sys
import time
import uuid
from datetime import datetime, timezone
from flask import Flask, Response, g, jsonify, request

app = Flask(__name__)

APP_NAME = "cloudledger"
APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
DEPLOY_SLOT = os.getenv("DEPLOY_SLOT", "stable")
DB_PATH = os.getenv("DB_PATH", "/tmp/cloudledger.db")
FAULT_RATE = float(os.getenv("FAULT_RATE", "0.0"))
START_TIME = time.time()

METRICS = {
    "requests_total": 0,
    "errors_total": 0,
    "latency_sum_seconds": 0.0,
}


def get_signing_key() -> str:
    return os.getenv("API_SIGNING_KEY", "dev-local-placeholder-key")


def secret_fingerprint() -> str:
    return hashlib.sha256(get_signing_key().encode("utf-8")).hexdigest()[:16]


def sign_payload(payload: str) -> str:
    return hmac.new(get_signing_key().encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()


def get_db():
    if "db" not in g:
        os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)
        g.db = sqlite3.connect(DB_PATH)
        g.db.execute("""CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tx_id TEXT UNIQUE NOT NULL,
                account TEXT NOT NULL,
                amount REAL NOT NULL,
                currency TEXT NOT NULL DEFAULT 'INR',
                signature TEXT NOT NULL,
                created_at TEXT NOT NULL
            )""")
        g.db.commit()
    return g.db


@app.teardown_appcontext
def close_db(_exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


@app.before_request
def before_req():
    g.req_start = time.time()
    g.trace_id = request.headers.get("X-Trace-Id", uuid.uuid4().hex[:12])
    if request.path not in ("/health", "/ready", "/metrics") and FAULT_RATE > 0.0:
        if random.random() < FAULT_RATE:
            METRICS["requests_total"] += 1
            METRICS["errors_total"] += 1
            return jsonify({"error": "injected_canary_fault", "version": APP_VERSION, "slot": DEPLOY_SLOT}), 500


@app.after_request
def after_req(resp):
    dur = max(time.time() - getattr(g, "req_start", time.time()), 0.0)
    if request.path != "/metrics":
        METRICS["requests_total"] += 1
        METRICS["latency_sum_seconds"] += dur
        if resp.status_code >= 500:
            METRICS["errors_total"] += 1
        log_entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": "ERROR" if resp.status_code >= 500 else "INFO",
            "service": APP_NAME,
            "version": APP_VERSION,
            "slot": DEPLOY_SLOT,
            "method": request.method,
            "path": request.path,
            "status": resp.status_code,
            "latency_ms": round(dur * 1000.0, 2),
            "trace_id": getattr(g, "trace_id", "none"),
        }
        print(json.dumps(log_entry), file=sys.stdout, flush=True)
    resp.headers["X-App-Version"] = APP_VERSION
    resp.headers["X-Deploy-Slot"] = DEPLOY_SLOT
    resp.headers["X-Trace-Id"] = getattr(g, "trace_id", "none")
    return resp


@app.route("/")
def index():
    return jsonify({
        "service": "CloudLedger",
        "app": APP_NAME,
        "version": APP_VERSION,
        "slot": DEPLOY_SLOT,
        "secret_fingerprint": secret_fingerprint(),
        "uptime_seconds": round(time.time() - START_TIME, 2),
    }), 200


@app.route("/health")
def health():
    return jsonify({"status": "UP", "service": APP_NAME, "version": APP_VERSION, "slot": DEPLOY_SLOT}), 200


@app.route("/ready")
def ready():
    try:
        conn = get_db()
        cnt = conn.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
        return jsonify({"ready": True, "db_records": cnt, "slot": DEPLOY_SLOT}), 200
    except Exception as exc:
        return jsonify({"ready": False, "error": str(exc)}), 503


@app.route("/metrics")
def metrics():
    try:
        cnt = get_db().execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
    except Exception:
        cnt = 0
    lines = [
        '# HELP cloudledger_http_requests_total Total HTTP requests served',
        '# TYPE cloudledger_http_requests_total counter',
        'cloudledger_http_requests_total{version="%s",slot="%s"} %d' % (APP_VERSION, DEPLOY_SLOT, METRICS["requests_total"]),
        '# HELP cloudledger_http_errors_total Total HTTP 5xx errors',
        '# TYPE cloudledger_http_errors_total counter',
        'cloudledger_http_errors_total{version="%s",slot="%s"} %d' % (APP_VERSION, DEPLOY_SLOT, METRICS["errors_total"]),
        '# HELP cloudledger_http_request_duration_seconds_sum Cumulative request latency in seconds',
        '# TYPE cloudledger_http_request_duration_seconds_sum counter',
        'cloudledger_http_request_duration_seconds_sum{version="%s",slot="%s"} %.6f' % (APP_VERSION, DEPLOY_SLOT, METRICS["latency_sum_seconds"]),
        '# HELP cloudledger_records_total Current persisted records in SQLite',
        '# TYPE cloudledger_records_total gauge',
        'cloudledger_records_total{slot="%s"} %d' % (DEPLOY_SLOT, cnt),
    ]
    return Response("\n".join(lines) + "\n", mimetype="text/plain; version=0.0.4")

@app.route("/api/transactions", methods=["GET", "POST"])
def transactions():
    conn = get_db()
    if request.method == "POST":
        data = request.get_json(force=True, silent=True) or {}
        tx_id = str(data.get("tx_id", "")).strip()
        account = str(data.get("account", "")).strip()
        amount = data.get("amount")
        currency = str(data.get("currency", "INR")).upper()
        if not tx_id or not account or amount is None:
            return jsonify({"error": "tx_id, account, and amount are required"}), 400
        try:
            amount = float(amount)
        except (TypeError, ValueError):
            return jsonify({"error": "amount must be numeric"}), 400
        payload = f"{tx_id}:{account}:{amount:.2f}:{currency}"
        sig = sign_payload(payload)
        now = datetime.now(timezone.utc).isoformat()
        conn.execute(
            "INSERT OR REPLACE INTO transactions (tx_id, account, amount, currency, signature, created_at) VALUES (?,?,?,?,?,?)",
            (tx_id, account, amount, currency, sig, now),
        )
        conn.commit()
        return jsonify({
            "status": "committed",
            "tx_id": tx_id,
            "account": account,
            "amount": amount,
            "currency": currency,
            "signature": sig[:16],
            "slot": DEPLOY_SLOT,
        }), 201

    rows = conn.execute(
        "SELECT tx_id, account, amount, currency, signature, created_at FROM transactions ORDER BY id ASC"
    ).fetchall()
    items = [
        {"tx_id": r[0], "account": r[1], "amount": r[2], "currency": r[3], "signature": r[4][:16], "created_at": r[5]}
        for r in rows
    ]
    return jsonify({"count": len(items), "slot": DEPLOY_SLOT, "version": APP_VERSION, "transactions": items}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")))
