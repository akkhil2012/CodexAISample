# Character Identifier

Character Identifier is a production-ready starter app that accepts an uploaded image and returns the most likely fictional character identity with confidence, notes, and warnings. The system uses deterministic image embeddings (placeholder for CLIP/SigLIP) and compares them against a reference gallery stored in a vector database.

## Features

- React frontend with drag-and-drop upload, preview, and results view.
- FastAPI backend with `/api/identify` inference endpoint and admin upload flow.
- Qdrant vector database (with local JSON fallback if Qdrant is not configured).
- Basic auth for admin endpoints.
- Rate limiting, file validation, and configurable confidence thresholds.

## Quickstart (Docker)

```bash
docker compose up --build
```

- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- Qdrant: http://localhost:6333

## Local Development

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## API Usage

### Identify a character

```bash
curl -X POST http://localhost:8000/api/identify \
  -F "file=@/path/to/image.png"
```

Response:

```json
{
  "request_id": "uuid",
  "top_predictions": [
    {
      "label": "Character Name",
      "confidence": 0.87,
      "notes": "Key visual cues...",
      "source": "custom dataset"
    }
  ],
  "model_version": "v1",
  "latency_ms": 1234,
  "warnings": ["low_confidence"]
}
```

### Add a character (admin)

```bash
curl -X POST http://localhost:8000/api/admin/identities \
  -u admin:admin \
  -F "label=Kara Starsong" \
  -F "notes=Blue jacket with star emblem" \
  -F "tags=hero,anime" \
  -F "file=@/path/to/reference.png"
```

## Scoring & Matching

1. The backend computes a deterministic embedding for the uploaded image (swap this with CLIP/SigLIP in production).
2. Embeddings are compared against stored vectors in Qdrant (or a JSON fallback store).
3. Results are ranked by cosine similarity and returned with notes, metadata, and warnings.

If the top confidence score falls below `CHARACTER_ID_LOW_CONFIDENCE_THRESHOLD` (default `0.4`), the API returns a `low_confidence` warning and the UI displays a safety note.

## Configuration

Environment variables (prefix: `CHARACTER_ID_`):

- `ADMIN_USER` / `ADMIN_PASSWORD`: Admin credentials for uploads.
- `MAX_UPLOAD_MB`: Maximum upload size (default 10).
- `LOW_CONFIDENCE_THRESHOLD`: Confidence threshold for warnings.
- `QDRANT_URL`: Use Qdrant when set (e.g., `http://qdrant:6333`).

## Tests

```bash
cd backend
pytest
```

## Deployment Notes

- Frontend can be deployed on Vercel or Netlify; set API proxy to your backend base URL.
- Backend can be deployed on Render or Fly.io with Qdrant running as a managed service.
