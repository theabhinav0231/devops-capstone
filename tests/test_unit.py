import os
import tempfile
import pytest
from app.app import app


@pytest.fixture
def client():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    os.environ["DB_PATH"] = path
    os.environ["API_SIGNING_KEY"] = "test-vault-signing-key-v1"
    import app.app as mod
    mod.DB_PATH = path
    mod.FAULT_RATE = 0.0
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c
    if os.path.exists(path):
        os.remove(path)


def test_health_returns_up(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.get_json()["status"] == "UP"


def test_ready_probe(client):
    r = client.get("/ready")
    assert r.status_code == 200
    assert r.get_json()["ready"] is True


def test_index_has_secret_fingerprint_not_plaintext(client):
    r = client.get("/")
    assert r.status_code == 200
    body = r.get_json()
    assert len(body["secret_fingerprint"]) == 16
    assert "test-vault-signing-key-v1" not in r.get_data(as_text=True)


def test_create_and_list_transactions(client):
    p = client.post("/api/transactions", json={"tx_id": "TX-9001", "account": "ACC-101", "amount": 2500.50, "currency": "INR"})
    assert p.status_code == 201
    assert len(p.get_json()["signature"]) == 16
    g = client.get("/api/transactions")
    assert g.status_code == 200
    assert g.get_json()["count"] == 1


def test_validation_rejects_bad_payload(client):
    p = client.post("/api/transactions", json={"tx_id": "TX-BAD"})
    assert p.status_code == 400


def test_prometheus_metrics_exposed(client):
    client.get("/health")
    m = client.get("/metrics")
    assert m.status_code == 200
    txt = m.get_data(as_text=True)
    assert "cloudledger_http_requests_total" in txt
    assert "cloudledger_records_total" in txt
