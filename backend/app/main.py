from __future__ import annotations

import io
import time
import uuid
from collections import defaultdict, deque

from fastapi import Depends, FastAPI, File, HTTPException, Request, UploadFile, status
from fastapi.responses import JSONResponse
from PIL import Image

from .auth import require_admin
from .config import settings
from .embeddings import compute_embedding
from .store import get_store

app = FastAPI(title="Character Identifier API", version="1.0")
store = get_store()
rate_limiter: dict[str, deque[float]] = defaultdict(deque)


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    if request.url.path.startswith("/api/"):
        ip = request.client.host if request.client else "unknown"
        now = time.time()
        window = settings.request_rate_window_seconds
        limit = settings.request_rate_limit
        queue = rate_limiter[ip]
        while queue and queue[0] < now - window:
            queue.popleft()
        if len(queue) >= limit:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Rate limit exceeded"},
            )
        queue.append(now)
    return await call_next(request)


@app.post("/api/identify")
async def identify(file: UploadFile = File(...)) -> dict:
    if not file.content_type or file.content_type.lower() not in {
        "image/jpeg",
        "image/png",
        "image/webp",
    }:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    contents = await file.read()
    max_bytes = settings.max_upload_mb * 1024 * 1024
    if len(contents) > max_bytes:
        raise HTTPException(status_code=400, detail="File exceeds 10MB limit")

    try:
        Image.open(io.BytesIO(contents)).verify()
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid image file") from exc

    start = time.perf_counter()
    embedding = compute_embedding(contents)
    matches = store.query(embedding, settings.top_k)
    latency_ms = int((time.perf_counter() - start) * 1000)

    warnings: list[str] = []
    predictions = []
    if not matches:
        warnings.append("no_reference_data")
    else:
        for match in matches:
            predictions.append(
                {
                    "label": match["label"],
                    "confidence": round(match["score"], 4),
                    "notes": match.get("notes", ""),
                    "source": match.get("source", "custom dataset"),
                }
            )
        if predictions and predictions[0]["confidence"] < settings.low_confidence_threshold:
            warnings.append("low_confidence")

    if not predictions:
        predictions.append(
            {
                "label": "Unknown",
                "confidence": 0.0,
                "notes": "No reference embeddings available yet.",
                "source": "custom dataset",
            }
        )

    return {
        "request_id": str(uuid.uuid4()),
        "top_predictions": predictions,
        "model_version": "v1",
        "latency_ms": latency_ms,
        "warnings": warnings,
    }


@app.post("/api/admin/identities", dependencies=[Depends(require_admin)])
async def add_identity(
    label: str,
    notes: str,
    tags: str | None = None,
    file: UploadFile = File(...),
) -> dict:
    if not file.content_type or file.content_type.lower() not in {
        "image/jpeg",
        "image/png",
        "image/webp",
    }:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    contents = await file.read()
    max_bytes = settings.max_upload_mb * 1024 * 1024
    if len(contents) > max_bytes:
        raise HTTPException(status_code=400, detail="File exceeds 10MB limit")

    try:
        Image.open(io.BytesIO(contents)).verify()
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid image file") from exc

    embedding = compute_embedding(contents)
    tag_list = [tag.strip() for tag in tags.split(",")] if tags else []
    record = store.add_identity(label=label, embedding=embedding, notes=notes, tags=tag_list)

    return {"id": record["id"], "label": label, "tags": tag_list}
