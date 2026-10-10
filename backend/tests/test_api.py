import io
import os

os.environ["DEDUPE_IMAGES"] = "true"

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)
JPG = b"\xff\xd8\xff\xe0" + b"0" * 100
PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 100
SOLUTION = "Fill the pothole and resurface the road."


def post(data=JPG, ctype="image/jpeg", slot="safety_infrastructure", solution=SOLUTION):
    return client.post(
        "/api/analyze",
        files={"image": ("p.jpg", io.BytesIO(data), ctype)},
        data={"location": "Rohini, Delhi", "quest_slot": slot, "user_solution": solution},
    )


def test_health():
    assert client.get("/api/health").json() == {"status": "ok"}


def test_quest():
    r = client.post("/api/quest", json={"location": "Rohini, Delhi"})
    assert r.status_code == 200 and len(r.json()["slots"]) == 3


def test_quest_empty_location():
    assert client.post("/api/quest", json={"location": " "}).status_code == 422


def test_analyze_ok_and_total_is_backend_sum():
    r = post(JPG + b"a")
    assert r.status_code == 200
    s = r.json()["score"]
    assert s["total"] == s["problem_validity"] + s["solution_quality"] + s["bonus"]


def test_png_ok():
    assert post(PNG, "image/png", slot="cleanliness_environment").status_code == 200


def test_bad_type():
    assert post(b"hello", "text/plain").status_code == 415


def test_fake_image_rejected():
    assert post(b"not really an image", "image/jpeg").status_code == 415


def test_too_large():
    assert post(JPG + b"0" * (9 * 1024 * 1024)).status_code == 413


def test_duplicate_rejected():
    img = JPG + b"unique-dup"
    assert post(img).status_code == 200
    assert post(img).status_code == 409


def test_bad_slot():
    assert post(JPG + b"z", slot="potholes").status_code == 422


def test_short_solution():
    assert post(JPG + b"y", solution="fix").status_code == 422


def test_find_channel():
    r = client.post("/api/find-channel", json={
        "location": "Rohini, Delhi", "issue_type": "pothole", "authority": "Municipal road authority"})
    assert r.status_code == 200 and r.json()["bonus"] == 2
