import base64
import io

from fastapi.testclient import TestClient
from PIL import Image

from app.main import app

client = TestClient(app)


def make_image_bytes(color: str = "blue") -> bytes:
    image = Image.new("RGB", (32, 32), color=color)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def test_add_identity_and_identify():
    image_bytes = make_image_bytes()
    response = client.post(
        "/api/admin/identities",
        auth=("admin", "admin"),
        data={"label": "Test Hero", "notes": "Blue outfit", "tags": "hero,blue"},
        files={"file": ("hero.png", image_bytes, "image/png")},
    )
    assert response.status_code == 200

    identify_response = client.post(
        "/api/identify",
        files={"file": ("hero.png", image_bytes, "image/png")},
    )
    assert identify_response.status_code == 200
    payload = identify_response.json()
    assert payload["top_predictions"]
    assert payload["top_predictions"][0]["label"] in {"Test Hero", "Unknown"}


def test_rejects_bad_type():
    data = base64.b64encode(b"not-an-image")
    response = client.post(
        "/api/identify",
        files={"file": ("bad.txt", data, "text/plain")},
    )
    assert response.status_code == 400
