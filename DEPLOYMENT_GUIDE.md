# Deployment Guide

This guide walks you through deploying the Tournament Scheduler application with the backend on Render and frontend on Vercel.

## Prerequisites

- GitHub account
- Render account (https://render.com)
- Vercel account (https://vercel.com)
- Your code pushed to a GitHub repository

## Backend Deployment on Render

### Step 1: Push Your Code to GitHub

```bash
git add .
git commit -m "Add deployment configurations"
git push origin main
```

### Step 2: Create a New Web Service on Render

1. Go to https://dashboard.render.com
2. Click "New +" and select "Web Service"
3. Connect your GitHub repository
4. Configure the service:
   - **Name**: `tournament-scheduler-api` (or your preferred name)
   - **Region**: Choose closest to your users
   - **Branch**: `main`
   - **Root Directory**: Leave empty
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r backend/requirements.txt`
   - **Start Command**: `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type**: Free (or paid for better performance)

5. Add Environment Variables (if needed):
   - Click "Advanced" and add any environment variables

6. Click "Create Web Service"

### Step 3: Wait for Deployment

Render will build and deploy your backend. Once complete, you'll get a URL like:
```
https://tournament-scheduler-api.onrender.com
```

### Step 4: Test Your Backend

Visit your Render URL + `/health`:
```
https://tournament-scheduler-api.onrender.com/health
```

You should see: `{"status":"ok","message":"Tournament Scheduler API is running."}`

## Frontend Deployment on Vercel

### Step 1: Update Frontend API Configuration

Before deploying, you need to update the frontend to use environment variables for the API URL.

1. Create a `.env.production` file in the `frontend` directory:

```bash
VITE_API_BASE_URL=https://your-render-app.onrender.com
```

Replace `your-render-app.onrender.com` with your actual Render backend URL.

2. Update your frontend components to use the environment variable. Check files in `frontend/src/components/` and replace hardcoded API URLs with:

```javascript
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
```

### Step 2: Deploy to Vercel

#### Option A: Using Vercel CLI

1. Install Vercel CLI:
```bash
npm install -g vercel
```

2. Navigate to your project root:
```bash
cd /path/to/your/project
```

3. Deploy:
```bash
vercel
```

4. Follow the prompts:
   - Set up and deploy? `Y`
   - Which scope? Select your account
   - Link to existing project? `N`
   - Project name? `tournament-scheduler`
   - In which directory is your code located? `./`
   - Want to override settings? `Y`
   - Build Command: `cd frontend && npm install && npm run build`
   - Output Directory: `frontend/dist`
   - Development Command: Leave default

5. Set environment variable:
```bash
vercel env add VITE_API_BASE_URL
```
Enter your Render backend URL when prompted.

6. Deploy to production:
```bash
vercel --prod
```

#### Option B: Using Vercel Dashboard

1. Go to https://vercel.com/dashboard
2. Click "Add New..." → "Project"
3. Import your GitHub repository
4. Configure the project:
   - **Framework Preset**: Vite
   - **Root Directory**: `./` (leave as is)
   - **Build Command**: `cd frontend && npm install && npm run build`
   - **Output Directory**: `frontend/dist`
   - **Install Command**: `npm install`

5. Add Environment Variables:
   - Click "Environment Variables"
   - Add `VITE_API_BASE_URL` with your Render backend URL
   - Example: `https://tournament-scheduler-api.onrender.com`

6. Click "Deploy"

### Step 3: Verify Deployment

Once deployed, Vercel will provide a URL like:
```
https://tournament-scheduler.vercel.app
```

Visit the URL and test the application.

## Post-Deployment Configuration

### Update CORS Settings (if needed)

If you encounter CORS errors, update the backend `main.py` to include your Vercel domain:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://tournament-scheduler.vercel.app",
        "http://localhost:5173",
        "http://localhost:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Redeploy the backend after making this change.

## Troubleshooting

### Backend Issues

1. **Build fails on Render**:
   - Check the build logs in Render dashboard
   - Verify `requirements.txt` has all dependencies
   - Ensure Python version is compatible (3.11+)

2. **Service crashes on startup**:
   - Check the logs in Render dashboard
   - Verify the start command is correct
   - Check for missing environment variables

3. **API returns 404**:
   - Verify the start command includes `cd backend`
   - Check that all Python files are in the `backend` directory

### Frontend Issues

1. **Build fails on Vercel**:
   - Check build logs in Vercel dashboard
   - Verify `package.json` has all dependencies
   - Ensure build command is correct

2. **API calls fail**:
   - Verify `VITE_API_BASE_URL` environment variable is set correctly
   - Check browser console for CORS errors
   - Ensure backend CORS settings include your Vercel domain

3. **404 on page refresh**:
   - Verify `vercel.json` has the correct rewrite rules
   - Check that SPA routing is configured properly

## Custom Domains (Optional)

### Render Custom Domain

1. Go to your service settings in Render
2. Click "Custom Domain"
3. Add your domain and follow DNS configuration instructions

### Vercel Custom Domain

1. Go to your project settings in Vercel
2. Click "Domains"
3. Add your domain and follow DNS configuration instructions

## Monitoring and Logs

### Render

- View logs: Dashboard → Your Service → Logs
- Monitor metrics: Dashboard → Your Service → Metrics

### Vercel

- View deployment logs: Dashboard → Your Project → Deployments → Select deployment
- Monitor analytics: Dashboard → Your Project → Analytics

## Cost Considerations

### Render Free Tier

- Services spin down after 15 minutes of inactivity
- First request after spin-down may take 30-60 seconds
- 750 hours/month free

### Vercel Free Tier

- 100 GB bandwidth/month
- Unlimited deployments
- Serverless function execution limits apply

## Upgrading to Paid Plans

For production use with better performance:

- **Render**: Upgrade to Starter ($7/month) or higher for always-on service
- **Vercel**: Upgrade to Pro ($20/month) for higher limits and better support

## Next Steps

1. Set up continuous deployment (auto-deploy on git push)
2. Configure custom domains
3. Set up monitoring and alerts
4. Implement proper error tracking (e.g., Sentry)
5. Add analytics (e.g., Google Analytics, Plausible)

## Support

- Render Documentation: https://render.com/docs
- Vercel Documentation: https://vercel.com/docs
- Project Issues: Create an issue in your GitHub repository
