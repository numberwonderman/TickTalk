# TickTalk

Image-first **triage** for possible Lyme disease rashes (e.g. erythema
migrans / "bullseye" rash). Built for the OpenCV AI Competition, powered by
AWS (build phase ends Oct 26, 2026). Solo project by Franklin since Sep
22, 2026. See `docs/BUILD_PLAN.md` for what changed.

**TickTalk never diagnoses.** It takes a photo (primary input) plus a few
supplementary details — tick exposure, how long the rash has been there,
fever — and returns a triage recommendation: how urgently to see a doctor.
When it's uncertain, it escalates. It never tells anyone they're "probably
fine." See `backend/app/triage/levels.py` for the exact three outcomes and
`docs/ARCHITECTURE.md` for why the system is built this way.

## Repo layout

```
backend/    FastAPI app: OpenCV pipeline, swappable vision model, triage engine, API
frontend/   React + Vite + TypeScript upload/questionnaire/results UI
infra/      AWS notes (nothing provisioned yet)
docs/       Architecture, dataset research, competition open questions, build plan
```

Start with `docs/ARCHITECTURE.md` for the full system design and the
alternatives we considered, `docs/DATASETS.md` for dataset candidates and
licensing, `docs/OPEN_QUESTIONS.md` for what we still need to confirm
against the official competition rules, and `docs/BUILD_PLAN.md` for the
milestone plan back from Oct 24.

## Running locally

### Backend

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # defaults to the mock vision model, no AWS needed
uvicorn app.main:app --reload
```

Runs on `http://localhost:8000`. `/health` for a liveness check, `POST
/api/triage` for the triage endpoint (multipart image + form fields).

Run tests: `PYTHONPATH=. pytest tests/`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Runs on `http://localhost:5173` and proxies `/api` to the backend (see
`vite.config.ts`).

### Mobile (Capacitor)

The frontend is wrapped for native mobile via
[Capacitor](https://capacitorjs.com/) rather than rewritten in React
Native — reuses every component as-is, just adds native camera access
(`frontend/src/capacitor/camera.ts`) and app packaging.
`capacitor.config.ts` is already set up (`appId: com.ticktalk.app`), but
**native platform projects aren't generated in this repo** — this
environment has no Android SDK or Xcode, so `cap add` couldn't be
verified here. To build a native app locally, once you have the
toolchain installed:

```bash
cd frontend
npm run build
npx cap add android   # needs Android Studio / Android SDK
npx cap add ios        # needs Xcode, macOS only
npx cap sync
npx cap open android    # or: npx cap open ios
```

The web app (`npm run dev`) works exactly as before in a plain browser —
`UploadForm.tsx` falls back to a normal `<input type="file">` there and
only switches to the native camera picker when running inside the
Capacitor shell (`Capacitor.isNativePlatform()`).

### Both, via Docker

```bash
docker compose up --build
```

(Backend only for now — frontend is dev-server-first until we settle the
hosting approach in `docs/BUILD_PLAN.md` Milestone 5.)

## Vision model

The backend defaults to `VISION_MODEL_BACKEND=mock`, a deterministic
low-confidence stub, so the app runs end-to-end with no ML dependency
installed. The one real-model adapter is Qwen3-VL-8B,
`backend/app/vision/models/qwen3_vl_8b_adapter.py`
(`VISION_MODEL_BACKEND=qwen_local_8b`). It loads the model
**in-process** (in memory, not as an HTTP service), and it runs on a
RunPod spot GPU for the eval pass only. It isn't hosted as part of the
deployed app. The 32B adapter and the 8B-vs-32B benchmark were cut; see
`docs/BUILD_PLAN.md`, "Scope cuts". The adapter's TODOs list what's
still needed to wire it up. See `backend/app/vision/model_interface.py` for the interface
every model (current or future) implements — swapping models should
never require touching the triage engine.

## Status

Early scaffold. OpenCV preprocessing/segmentation/feature-extraction code
runs and is unit-tested at the triage-engine level, but segmentation
thresholds and the Qwen adapter are placeholders pending real image
validation — see `docs/BUILD_PLAN.md` Milestone 1.
