# Deploy to Railway — Step by Step

## Prerequisites

- A [Railway](https://railway.com) account
- Your API keys ready:
  - **OpenRouter API key** — from [openrouter.ai/keys](https://openrouter.ai/keys)
  - **Brave Search API key** — from [api-dashboard.search.brave.com](https://api-dashboard.search.brave.com)
- This repo pushed to GitHub at `gregdickson/skill-tester`

---

## Step 1: Create a New Railway Project

1. Go to [railway.com/new](https://railway.com/new)
2. Click **"Deploy from GitHub repo"**
3. Select `gregdickson/skill-tester`
4. Railway will detect the repo — don't deploy yet, we need to configure services first

---

## Step 2: Add PostgreSQL

1. In your Railway project, click **"+ New"** → **"Database"** → **"Add PostgreSQL"**
2. Railway provisions a Postgres 16 instance automatically
3. Click the Postgres service → **"Variables"** tab
4. Copy the `DATABASE_URL` value — you'll need it in Step 4
   - It will look like: `postgresql://postgres:xxxxx@xxxxx.railway.internal:5432/railway`

---

## Step 3: Configure the Backend Service

1. Click the GitHub service that was created (it may have auto-detected the repo)
2. Go to **"Settings"** tab:
   - **Root Directory**: `backend`
   - **Builder**: `Dockerfile`
   - **Start Command**: `alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
3. Go to **"Networking"** tab:
   - Click **"Generate Domain"** to get a public URL (e.g. `skill-tester-backend-production-xxxx.up.railway.app`)
   - Note this URL — the frontend needs it

---

## Step 4: Set Backend Environment Variables

Go to the backend service → **"Variables"** tab. Add these:

| Variable | Value |
|----------|-------|
| `DATABASE_URL` | Click **"Add Reference"** → select the Postgres service's `DATABASE_URL`. **Important:** change the scheme from `postgresql://` to `postgresql+asyncpg://` (add `+asyncpg` after `postgresql`) |
| `OPENROUTER_API_KEY` | Your OpenRouter API key |
| `BRAVE_API_KEY` | Your Brave Search API key |
| `DEFAULT_MODEL` | `moonshotai/kimi-k2` |
| `CORS_ORIGINS` | `https://your-frontend-domain.up.railway.app` (set this after Step 5) |

The `DATABASE_URL` reference will auto-resolve to the internal connection string. You just need to ensure it uses `postgresql+asyncpg://` as the scheme for SQLAlchemy async to work.

---

## Step 5: Add the Frontend Service

1. In your Railway project, click **"+ New"** → **"GitHub Repo"** → select the same repo
2. Go to **"Settings"** tab:
   - **Root Directory**: `frontend`
   - **Builder**: `Dockerfile`
3. Go to **"Networking"** tab:
   - Click **"Generate Domain"** (e.g. `skill-tester-frontend-production-xxxx.up.railway.app`)
4. Go to **"Variables"** tab:
   - Add `VITE_API_URL` = `https://your-backend-domain.up.railway.app` (the URL from Step 3)

**Important:** Go back to the backend service and update `CORS_ORIGINS` to include the frontend's domain from this step.

---

## Step 6: Update Frontend nginx.conf for Railway

The frontend's `nginx.conf` currently proxies to `http://backend:8000` which works for Docker Compose but not Railway. For Railway, the frontend needs to call the backend's public URL directly.

**Option A (Recommended): Client-side API calls**
The frontend already uses Vite's proxy in dev mode and relative `/api` paths. For production on Railway, update the frontend's `nginx.conf` to proxy to the backend's Railway internal URL:

In `frontend/nginx.conf`, change:
```
proxy_pass http://backend:8000;
```
to:
```
proxy_pass http://your-backend-service.railway.internal:PORT;
```

Where the internal URL and port come from the backend service's **"Networking"** → **"Private Networking"** section.

**Option B: Single service**
Deploy only the backend and serve the frontend build as static files from FastAPI. Simpler but less scalable.

---

## Step 7: Deploy

1. Railway auto-deploys on push to `main` by default
2. Push your code: `git push origin main`
3. Watch the build logs in Railway for both services
4. The backend will:
   - Install Python dependencies
   - Run `alembic upgrade head` (creates all 9 database tables)
   - Start the FastAPI server
5. The frontend will:
   - Install npm dependencies
   - Build the React app
   - Serve via nginx

---

## Step 8: Verify

1. Hit `https://your-backend-domain.up.railway.app/api/health` — should return `{"status": "ok"}`
2. Hit `https://your-backend-domain.up.railway.app/docs` — should show the FastAPI OpenAPI docs
3. Open `https://your-frontend-domain.up.railway.app` — should show the MicroGrad UI
4. Create a network and verify AI auto-population works (tests OpenRouter + Brave)

---

## Troubleshooting

**Backend won't start:**
- Check the build logs for Python import errors
- Verify `DATABASE_URL` has `+asyncpg` in the scheme
- Ensure the Postgres service is running

**Alembic migration fails:**
- Check that the Postgres service is fully provisioned before the backend starts
- You may need to add a sleep or health check dependency

**Frontend can't reach backend:**
- Verify `CORS_ORIGINS` includes the frontend domain (with `https://`)
- Check nginx proxy config points to the correct backend URL
- Look at browser console for CORS errors

**OpenRouter calls fail:**
- Verify your API key is valid at [openrouter.ai/keys](https://openrouter.ai/keys)
- Check you have credits loaded (free tier is very limited)
- Verify the model ID `moonshotai/kimi-k2` is available on OpenRouter

**Brave Search fails:**
- Verify your API key at [api-dashboard.search.brave.com](https://api-dashboard.search.brave.com)
- Brave requires a paid plan ($5/month minimum)

---

## Local Development (Alternative)

If you want to run locally instead:

```bash
# Start Postgres
docker-compose up db -d

# Backend
cd backend
cp .env.example .env
# Edit .env with your API keys
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

Open http://localhost:5173
