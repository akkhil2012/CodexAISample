from __future__ import annotations

import json
import uuid
from pathlib import Path

from qdrant_client import QdrantClient
from qdrant_client.http import models as qdrant_models

from .config import settings
from .embeddings import cosine_similarity


class VectorStore:
    def add_identity(
        self,
        label: str,
        embedding: list[float],
        notes: str,
        tags: list[str] | None = None,
        source: str = "custom dataset",
    ) -> dict:
        raise NotImplementedError

    def query(self, embedding: list[float], limit: int) -> list[dict]:
        raise NotImplementedError


class LocalStore(VectorStore):
    def __init__(self, path: str) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text(json.dumps({"items": []}, indent=2), encoding="utf-8")

    def _load(self) -> dict:
        return json.loads(self.path.read_text(encoding="utf-8"))

    def _save(self, data: dict) -> None:
        self.path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def add_identity(
        self,
        label: str,
        embedding: list[float],
        notes: str,
        tags: list[str] | None = None,
        source: str = "custom dataset",
    ) -> dict:
        data = self._load()
        item = {
            "id": str(uuid.uuid4()),
            "label": label,
            "embedding": embedding,
            "notes": notes,
            "tags": tags or [],
            "source": source,
        }
        data["items"].append(item)
        self._save(data)
        return item

    def query(self, embedding: list[float], limit: int) -> list[dict]:
        data = self._load()
        scored = []
        for item in data.get("items", []):
            score = cosine_similarity(embedding, item["embedding"])
            scored.append({**item, "score": score})
        scored.sort(key=lambda entry: entry["score"], reverse=True)
        return scored[:limit]


class QdrantStore(VectorStore):
    def __init__(self, url: str, collection: str) -> None:
        self.client = QdrantClient(url=url)
        self.collection = collection
        if collection not in [c.name for c in self.client.get_collections().collections]:
            self.client.create_collection(
                collection_name=collection,
                vectors_config=qdrant_models.VectorParams(size=256, distance=qdrant_models.Distance.COSINE),
            )

    def add_identity(
        self,
        label: str,
        embedding: list[float],
        notes: str,
        tags: list[str] | None = None,
        source: str = "custom dataset",
    ) -> dict:
        item_id = str(uuid.uuid4())
        payload = {
            "label": label,
            "notes": notes,
            "tags": tags or [],
            "source": source,
        }
        self.client.upsert(
            collection_name=self.collection,
            points=[qdrant_models.PointStruct(id=item_id, vector=embedding, payload=payload)],
        )
        return {"id": item_id, **payload, "embedding": embedding}

    def query(self, embedding: list[float], limit: int) -> list[dict]:
        results = self.client.search(
            collection_name=self.collection,
            query_vector=embedding,
            limit=limit,
        )
        items = []
        for result in results:
            payload = result.payload or {}
            items.append(
                {
                    "id": str(result.id),
                    "label": payload.get("label", "Unknown"),
                    "notes": payload.get("notes", ""),
                    "tags": payload.get("tags", []),
                    "source": payload.get("source", "custom dataset"),
                    "score": float(result.score),
                }
            )
        return items


def get_store() -> VectorStore:
    if settings.qdrant_url:
        return QdrantStore(settings.qdrant_url, settings.qdrant_collection)
    return LocalStore(settings.data_path)
