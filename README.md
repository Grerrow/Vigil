# Vigil

Vigil is a real-time person detection and counting system built with YOLOv8, FastAPI, and React.

## Why Vigil

- Production-style split architecture (API + client)
- Fast person detection with YOLOv8
- Persistent detection history with filtering
- Docker and local development workflows

## Stack

- **Backend:** FastAPI, Ultralytics YOLOv8, OpenCV, SQLModel, SQLite
- **Frontend:** React, Vite, Axios, Recharts
- **Runtime:** Python 3.11+, Node.js 20+, Docker Compose (optional)

## Architecture

```text
repo/
├── backend/
│   ├── main.py
│   ├── db.py
│   ├── models/
│   ├── routes/
│   └── utils/
├── frontend/
│   ├── src/
│   └── public/
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

## Features

- Image upload and person detection (`/detect`)
- Bounding box overlays with per-person confidence
- Summary metrics (count, average confidence, inference time)
- Detection history storage (`/history`)
- History filtering by date range and minimum confidence
- History reset endpoint (`/reset`)
- History visualization chart in the UI

## API

| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | Service health check |
| `/detect` | POST | Detect people from an uploaded image |
| `/history` | GET | Return stored detections with optional filters |
| `/reset` | POST | Clear stored detection history |

## Quick start (Docker)

```bash
docker compose up --build
```

- Frontend: `http://localhost:5173`
- Backend: `http://localhost:8000`
- Swagger: `http://localhost:8000/docs`

### Persistence note

The backend stores SQLite data at:

- container path: `/app/data/vigil.db`
- host path (through bind mount): `backend/data/vigil.db`

## Quick start (Local)

### 1) Backend

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 2) Frontend

```bash
cd frontend
npm install
npm run dev
```

## Environment variables

Example values are in `.env.example`.

| Variable | Purpose |
|---|---|
| `HOST` | Backend bind host |
| `PORT` | Backend port |
| `MODEL_NAME` | YOLO model weights |
| `CONFIDENCE_THRESHOLD` | Detection threshold |
| `DATABASE_PATH` | SQLite database file path |
| `VITE_API_BASE_URL` | Frontend API base URL |


## Features to be added

- Video file scanning with frame-by-frame detection
- Live webcam and RTSP/CCTV stream ingestion with overlays
- Multi-camera management and per-camera tracking
- Face recognition pipeline with identity events stored in the database
- Zone/region alerts (for restricted area occupancy thresholds)
- Heatmaps and movement-density visualization
- Time-based analytics dashboard (hourly/daily crowd patterns)
- CSV/Excel export for history and analytics
- Edge/desktop packaging for camera-side deployments

## Notes on face recognition

Face recognition should be implemented with explicit user consent, retention policies,
and jurisdiction-specific privacy compliance controls before production deployment.
