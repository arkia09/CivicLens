
https://github.com/user-attachments/assets/d60d4a43-1380-4630-a747-a66f4f71aaa0
<p align="center">
  <img src="frontend/public/mascot.webp" alt="Civic Lens mascot" width="120" />
</p>

<h1 align="center">Civic Lens</h1>

<p align="center">
  Photograph three real problems in your neighbourhood, propose a fix, and get a score,
  the responsible authority and a ready-to-send complaint.
</p>

<p align="center">
  <a href="LIVE_URL">Live app</a> ·
  <a href="DEV_POST_URL">DEV post</a>
</p>

Built for the [Hacktoberfest Open-Source AI Challenge, Week 1: Touch Grass](https://dev.to/challenges/hacktoberfest-week1-2026-10-05).
The backend is on a free Render plan and sleeps when idle, so the first request can be slow.

## Demo Video

https://github.com/user-attachments/assets/c9878c09-e639-4ffe-b173-df043ea9aab5



## Features

- Gemma writes a short quest for your area, with one hint for each of three categories.
- Upload a photo and your proposed fix. Gemma checks the photo, scores the problem and your fix,
  names the kind of authority responsible, and drafts a complaint.
- SerpApi looks for an official government reporting page (`.gov.in` / `.nic.in`) for a +2 bonus.

## Tech stack

- **Backend:** FastAPI, Pydantic, httpx, Pillow
- **Frontend:** React, TypeScript, Vite, Tailwind CSS
- **AI:** Gemma via the `google-genai` SDK
- **Search:** SerpApi
- **Hosting:** Render

## Project structure

```
civiclens/
├── backend/
│   ├── main.py        # API routes
│   ├── gemma.py       # Gemma calls, JSON parsing, retries
│   ├── search.py      # SerpApi lookup, cache, daily cap
│   ├── prompts.py     # prompt text
│   ├── models.py      # Pydantic models (API contract)
│   ├── utils.py       # image checks, duplicate detection, scoring
│   ├── mock_data.py   # canned data for frontend work
│   └── tests/
├── frontend/
│   ├── public/
│   └── src/
│       ├── App.tsx, api.ts, points.ts, types.ts
│       └── components/
└── render.yaml
```

API routes: `GET /api/health`, `POST /api/quest`, `POST /api/analyze`, `POST /api/find-channel`.

## Run locally

Requires Python 3.10+ and Node 20+. Clone the repo, then:

### Backend

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
cd backend
pip install -r requirements.txt
```

Create `backend/.env`:

```
GEMMA_API_KEY=your_google_ai_key
SERPAPI_KEY=your_serpapi_key
```

Start the server from inside the `backend` folder:

```bash
uvicorn main:app --reload --port 8000
```

It runs at `http://localhost:8000`. To work without API keys, add `USE_MOCK=true` to `.env`.

### Frontend

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. The frontend calls `http://localhost:8000` by default. To use a
different backend, create `frontend/.env` with `VITE_API_URL=https://your-backend-url` (no trailing slash).

### Tests

```bash
cd backend
pytest
```

## Configuration

Backend environment variables (all optional except the two keys):

| Variable | Default | Purpose |
| --- | --- | --- |
| `GEMMA_API_KEY` | none | Google AI key for Gemma (required) |
| `SERPAPI_KEY` | none | SerpApi key (required for channel lookup) |
| `CORS_ORIGINS` | `http://localhost:5173` | Allowed frontend origins, comma-separated |
| `GEMMA_MODEL` | `gemma-4-26b-a4b-it` | Primary model |
| `GEMMA_FALLBACK_MODEL` | `gemma-4-31b-it` | Used if the primary fails |
| `USE_MOCK` | `false` | Serve canned data, no external calls |
| `DEDUPE_IMAGES` | `true` | Reject photos already scored |
| `MAX_IMAGE_MB` | `8` | Upload size limit |
| `SEARCH_DAILY_LIMIT` | `50` | Max SerpApi calls per day |

## Deployment

Deployed on Render as two services: a Python web service (root `backend`) and a static site
(root `frontend`, publish directory `dist`). See `render.yaml` for the settings.

## License

MIT. See [LICENSE](LICENSE).
