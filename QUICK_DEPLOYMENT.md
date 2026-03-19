# Quick Deployment Checklist

## 1. Prepare Your Repository

```bash
# Make sure all changes are committed
git add .
git commit -m "Add deployment configurations"
git push origin main
```

## 2. Deploy Backend to Render (5 minutes)

1. Go to https://dashboard.render.com/
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Fill in:
   - **Name**: `tournament-scheduler-api`
   - **Build Command**: `pip install -r backend/requirements.txt`
   - **Start Command**: `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Click "Create Web Service"
6. Wait for deployment (2-3 minutes)
7. Copy your backend URL (e.g., `https://tournament-scheduler-api.onrender.com`)

## 3. Update Frontend Environment Variable

Edit `frontend/.env.production` and replace with your Render URL:

```bash
VITE_API_BASE_URL=https://your-actual-render-url.onrender.com
```

Commit this change:

```bash
git add frontend/.env.production
git commit -m "Update production API URL"
git push origin main
```

## 4. Deploy Frontend to Vercel (3 minutes)

### Option A: Vercel CLI (Recommended)

```bash
# Install Vercel CLI globally
npm install -g vercel

# Deploy from project root
vercel

# Follow prompts, then deploy to production
vercel --prod
```

### Option B: Vercel Dashboard

1. Go to https://vercel.com/new
2. Import your GitHub repository
3. Configure:
   - **Root Directory**: `./`
   - **Build Command**: `cd frontend && npm install && npm run build`
   - **Output Directory**: `frontend/dist`
4. Add Environment Variable:
   - Key: `VITE_API_BASE_URL`
   - Value: Your Render backend URL
5. Click "Deploy"

## 5. Test Your Deployment

1. Visit your Vercel URL
2. Try generating a schedule
3. Check all visualizations load correctly

## Troubleshooting

### CORS Error?
Update `backend/main.py` line 30-37 to include your Vercel domain:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://your-vercel-app.vercel.app",
        "http://localhost:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Then redeploy on Render (it will auto-deploy if you push to GitHub).

### Backend Slow on First Request?
Render free tier spins down after 15 minutes of inactivity. First request takes 30-60 seconds to wake up. Upgrade to paid plan for always-on service.

## Done! 🎉

Your app is now live:
- Backend: `https://your-app.onrender.com`
- Frontend: `https://your-app.vercel.app`
