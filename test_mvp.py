#!/usr/bin/env python3
"""End-to-end tests for BuildTrack AI MVP."""

import json
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_root():
    resp = client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "running"
    print("✓ Root endpoint")


def test_material_full_flow():
    sid = "test_material"
    resp = client.post("/chat", json={"session_id": sid, "message": "Bought 500kg cement"})
    data = resp.json()
    assert data["status"] == "incomplete"
    assert data["entry_type"] == "material"
    assert data["extracted"]["material_name"] == "cement"
    assert data["extracted"]["quantity"] == 500.0
    assert data["extracted"]["unit"] == "kg"
    assert "project" in data["missing_fields"]
    assert data["current_question"] == "Which project is this for?"
    assert 0 <= data["confidence"] <= 1.0
    print("✓ Initial material parsing")

    resp = client.post("/chat", json={"session_id": sid, "message": "Sunrise Tower"})
    data = resp.json()
    assert data["status"] == "incomplete"
    assert data["extracted"]["project"] == "Sunrise Tower"
    assert "supplier" in data["missing_fields"]
    print("✓ Project collected")

    resp = client.post("/chat", json={"session_id": sid, "message": "ABC Traders"})
    data = resp.json()
    assert data["status"] == "incomplete"
    assert data["extracted"]["supplier"] == "ABC Traders"
    assert "rate" in data["missing_fields"]
    print("✓ Supplier collected")

    resp = client.post("/chat", json={"session_id": sid, "message": "450"})
    data = resp.json()
    assert data["status"] == "incomplete"
    assert data["extracted"]["rate"] == 450.0
    assert "floor" in data["missing_fields"]
    print("✓ Rate collected")

    resp = client.post("/chat", json={"session_id": sid, "message": "2"})
    data = resp.json()
    assert data["status"] == "incomplete"
    assert data["extracted"]["floor"] == "2"
    assert "activity" in data["missing_fields"]
    print("✓ Floor collected")

    resp = client.post("/chat", json={"session_id": sid, "message": "Foundation"})
    data = resp.json()
    assert data["status"] == "completed"
    assert data["summary"] is not None
    assert "Confirm save?" in data["summary"]
    print("✓ Activity collected, summary shown")

    resp = client.post("/chat", json={"session_id": sid, "message": "yes"})
    data = resp.json()
    assert data["status"] == "saved"
    print("✓ Entry saved")

    # Verify saved entry
    saved_path = os.path.join(os.path.dirname(__file__), "storage", "saved_entries.json")
    with open(saved_path) as f:
        entries = json.loads(f.read() or "[]")
    assert len(entries) >= 1
    last = entries[-1]
    assert last["entry_type"] == "material"
    assert last["data"]["material_name"] == "cement"
    print("✓ Saved entry verified in storage")


def test_labour_flow():
    sid = "test_labour"
    resp = client.post("/chat", json={"session_id": sid, "message": "Added 12 masons"})
    data = resp.json()
    assert data["entry_type"] == "labour"
    assert data["extracted"]["labour_type"] == "mason"
    assert data["extracted"]["worker_count"] == 12
    assert "incomplete" in data["status"]
    print("✓ Labour parsing")

    # Follow the system's question order (project → hours → floor → activity → rate)
    resp = client.post("/chat", json={"session_id": sid, "message": "Sunrise Tower"})
    assert resp.json()["extracted"]["project"] == "Sunrise Tower"
    assert resp.json()["current_question"] == "How many hours did they work?"

    resp = client.post("/chat", json={"session_id": sid, "message": "8"})
    assert resp.json()["extracted"]["hours"] == 8.0
    assert resp.json()["current_question"] == "Which floor is this for?"

    resp = client.post("/chat", json={"session_id": sid, "message": "2"})
    assert resp.json()["extracted"]["floor"] == "2"
    assert resp.json()["current_question"] == "What activity is this for?"

    resp = client.post("/chat", json={"session_id": sid, "message": "Foundation"})
    assert resp.json()["extracted"]["activity"] == "foundation"
    assert resp.json()["current_question"] == "What is the hourly rate?"

    resp = client.post("/chat", json={"session_id": sid, "message": "500"})
    data = resp.json()
    assert data["status"] == "completed"
    summary = data["summary"]
    assert "Labour Entry" in summary

    resp = client.post("/chat", json={"session_id": sid, "message": "yes"})
    assert resp.json()["status"] == "saved"
    print("✓ Labour flow complete")


def test_equipment_flow():
    sid = "test_equipment"
    resp = client.post("/chat", json={"session_id": sid, "message": "JCB worked 6 hours"})
    data = resp.json()
    assert data["entry_type"] == "equipment"
    assert data["extracted"]["equipment_name"] == "jcb"
    assert data["extracted"]["hours_used"] == 6.0
    print("✓ Equipment parsing")

    # Follow the system's question order (project → operator → floor → activity)
    resp = client.post("/chat", json={"session_id": sid, "message": "Sunrise Tower"})
    assert resp.json()["extracted"]["project"] == "Sunrise Tower"
    assert resp.json()["current_question"] == "Who operated it?"

    resp = client.post("/chat", json={"session_id": sid, "message": "Ramesh"})
    assert resp.json()["extracted"]["operator"] == "Ramesh"
    assert resp.json()["current_question"] == "Which floor is this for?"

    resp = client.post("/chat", json={"session_id": sid, "message": "Ground"})
    assert resp.json()["extracted"]["floor"] == "Ground"

    resp = client.post("/chat", json={"session_id": sid, "message": "Excavation"})
    data = resp.json()
    assert data["status"] == "completed"

    resp = client.post("/chat", json={"session_id": sid, "message": "yes"})
    assert resp.json()["status"] == "saved"
    print("✓ Equipment flow complete")


def test_unknown_input():
    resp = client.post("/chat", json={"session_id": "unknown", "message": "Hello world"})
    data = resp.json()
    assert data["status"] == "unknown"
    print("✓ Unknown input handled")


def test_session_endpoint():
    sid = "test_session"
    client.post("/chat", json={"session_id": sid, "message": "Bought 500kg cement"})
    resp = client.get(f"/session/{sid}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["session_id"] == sid
    assert data["state"]["entry_type"] == "material"
    print("✓ Session endpoint")


def test_reset_endpoint():
    sid = "test_reset"
    client.post("/chat", json={"session_id": sid, "message": "Bought 500kg cement"})
    resp = client.post(f"/reset/{sid}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["state"]["entry_type"] is None
    assert data["state"]["data"] == {}
    print("✓ Reset endpoint")


if __name__ == "__main__":
    test_root()
    test_unknown_input()
    test_material_full_flow()
    test_labour_flow()
    test_equipment_flow()
    test_session_endpoint()
    test_reset_endpoint()
    print("\n✓ ALL TESTS PASSED")
