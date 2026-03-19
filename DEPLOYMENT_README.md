# 🚀 Deployment Instructions

Complete guide to deploy your Tournament Scheduler to production.

## 📦 What You'll Deploy

- **Backend (Python/FastAPI)** → Render
- **Frontend (React/Vite)** → Vercel

## ⚡ Quick Start (10 minutes)

### Prerequisites

- GitHub account with your code pushed
- [Render account](https://render.com) (free)
- [Vercel account](https://vercel.com) (free)

### Step 1: Deploy Backend to Render

1. Visit [Render Dashboard](https://dashboard.render.com/)
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository
4. Configure:
   ```
   Name: tournament-scheduler-api
   Runtime: Python 3
   Build Command: pip install -r backend/requirements.txt
   Start Command: cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT
   ```
5. Click **"Create Web Service"**
6. Wait 2-3 minutes for deployment
7. **Copy your backend URL** (e.g., `https://tournament-scheduler-api.onrender.com`)

### Step 2: Configure Frontend

Update `frontend/.env.production` with your Render URL:

```bash
VITE_API_BASE_URL=https://your-actual-render-url.onrender.com
```

Commit and push:

```bash
git add frontend/.env.production
git commit -m "Update production API URL"
git push origin main
```

### Step 3: Deploy Frontend to Vercel

#### Option A: Using Vercel CLI (Recommended)

```bash
# Install Vercel CLI
npm install -g vercel

# Deploy
vercel

# Deploy to production
vercel --prod
```

#### Option B: Using Vercel Dashboard

1. Visit [Vercel Dashboard](https://vercel.com/new)
2. Click **"Import Project"**
3. Select your GitHub repository
4. Configure:
   ```
   Framework Preset: Vite
   Root Directory: ./
   Build Command: cd frontend && npm install && npm run build
   Output Directory: frontend/dist
   ```
5. Add Environment Variable:
   - **Name**: `VITE_API_BASE_URL`
   - **Value**: Your Render backend URL
6. Click **"Deploy"**

### Step 4: Test Your Deployment

1. Visit your Vercel URL
2. Generate a test schedule
3. Verify all visualizations work

## 🔧 Configuration Files Created

- `render.yaml` - Render deployment configuration
- `vercel.json` - Vercel deployment configuration
- `frontend/src/config/api.js` - Centralized API configuration
- `frontend/.env.production` - Production environment variables
- `frontend/.env.example` - Example environment variables
- `.gitignore` - Git ignore rules

## 🐛 Troubleshooting

### CORS Errors

If you see CORS errors in the browser console:

1. Edit `backend/main.py` (around line 30)
2. Update the CORS middleware:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://your-vercel-app.vercel.app",  # Add your Vercel URL
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

3. Commit and push (Render will auto-redeploy)

### Backend Slow on First Request

Render's free tier spins down after 15 minutes of inactivity. The first request after spin-down takes 30-60 seconds.

**Solutions:**
- Upgrade to Render's paid plan ($7/month) for always-on service
- Accept the cold start delay for free tier
- Use a service like [UptimeRobot](https://uptimerobot.com/) to ping your API every 5 minutes

### Build Fails on Render

Check the build logs in Render dashboard. Common issues:

- **Missing dependencies**: Verify `backend/requirements.txt` is complete
- **Python version**: Render uses Python 3.11 by default
- **Import errors**: Ensure all Python files are in the `backend/` directory

### Build Fails on Vercel

Check the build logs in Vercel dashboard. Common issues:

- **Wrong build command**: Ensure it includes `cd frontend`
- **Missing dependencies**: Verify `frontend/package.json` is complete
- **Environment variable**: Ensure `VITE_API_BASE_URL` is set

### API Calls Return 404

- Verify the backend URL in `frontend/.env.production`
- Check that the backend is running (visit `/health` endpoint)
- Ensure CORS is configured correctly

## 📊 Monitoring

### Render

- **Logs**: Dashboard → Your Service → Logs
- **Metrics**: Dashboard → Your Service → Metrics
- **Health Check**: Visit `https://your-app.onrender.com/health`

### Vercel

- **Deployment Logs**: Dashboard → Your Project → Deployments
- **Analytics**: Dashboard → Your Project → Analytics
- **Real-time Logs**: Use Vercel CLI: `vercel logs`

## 💰 Cost Breakdown

### Free Tier Limits

**Render Free:**
- 750 hours/month
- Services spin down after 15 minutes of inactivity
- 512 MB RAM
- Shared CPU

**Vercel Free:**
- 100 GB bandwidth/month
- Unlimited deployments
- Serverless functions: 100 GB-hours/month
- 6,000 build minutes/month

### Paid Plans (Optional)

**Render Starter ($7/month):**
- Always-on service (no spin-down)
- 512 MB RAM
- Better performance

**Vercel Pro ($20/month):**
- 1 TB bandwidth/month
- Priority support
- Advanced analytics

## 🔄 Continuous Deployment

Both Render and Vercel support automatic deployments:

1. **Render**: Auto-deploys on push to `main` branch
2. **Vercel**: Auto-deploys on push to any branch
   - `main` branch → Production
   - Other branches → Preview deployments

To enable:
- Render: Already enabled by default
- Vercel: Already enabled by default

## 🌐 Custom Domains (Optional)

### Add Custom Domain to Render

1. Go to your service settings
2. Click **"Custom Domain"**
3. Add your domain
4. Update DNS records as instructed

### Add Custom Domain to Vercel

1. Go to your project settings
2. Click **"Domains"**
3. Add your domain
4. Update DNS records as instructed

## 🔐 Environment Variables

### Backend (Render)

Currently, no environment variables are required. If you add database or API keys later:

1. Go to your service settings in Render
2. Click **"Environment"**
3. Add your variables
4. Service will auto-restart

### Frontend (Vercel)

Required:
- `VITE_API_BASE_URL` - Your Render backend URL

To add/update:

```bash
vercel env add VITE_API_BASE_URL
```

Or via dashboard:
1. Project Settings → Environment Variables
2. Add/edit variables
3. Redeploy for changes to take effect

## 📚 Additional Resources

- [Render Documentation](https://render.com/docs)
- [Vercel Documentation](https://vercel.com/docs)
- [FastAPI Deployment Guide](https://fastapi.tiangolo.com/deployment/)
- [Vite Production Build](https://vitejs.dev/guide/build.html)

## 🆘 Getting Help

1. Check the troubleshooting section above
2. Review deployment logs in Render/Vercel dashboards
3. Check browser console for frontend errors
4. Test backend directly: `curl https://your-app.onrender.com/health`

## ✅ Deployment Checklist

- [ ] Code pushed to GitHub
- [ ] Backend deployed to Render
- [ ] Backend URL copied
- [ ] `frontend/.env.production` updated
- [ ] Changes committed and pushed
- [ ] Frontend deployed to Vercel
- [ ] Environment variable set in Vercel
- [ ] CORS configured (if needed)
- [ ] Health check passes
- [ ] Test schedule generation works
- [ ] All visualizations load correctly

## 🎉 Success!

Your Tournament Scheduler is now live and accessible worldwide!

- **Backend API**: `https://your-app.onrender.com`
- **Frontend App**: `https://your-app.vercel.app`

Share your deployment URLs and start scheduling tournaments! 🏆
