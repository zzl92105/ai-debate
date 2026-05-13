# AI Debate

Vue + FastAPI + DeepSeek API based AI debate MVP.

## Features

- Create a debate from a topic, style, and round count
- Generate affirmative and negative speeches round by round
- Generate a neutral judge result with scores, winner, highlights, and flaws
- Run locally without an API key using deterministic mock responses

## Project Structure

```text
ai-debate/
  backend/      FastAPI service and DeepSeek integration
  frontend/     Vue 3 + Vite client
```

## Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

Set `DEEPSEEK_API_KEY` in `backend/.env` to use the real API. Without it, the backend returns mock debate content.

## Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

