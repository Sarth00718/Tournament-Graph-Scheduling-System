#!/bin/bash

# Deployment Helper Script for Tournament Scheduler
# This script helps you deploy to Render and Vercel

echo "🚀 Tournament Scheduler Deployment Helper"
echo "=========================================="
echo ""

# Check if git is clean
if [[ -n $(git status -s) ]]; then
    echo "⚠️  You have uncommitted changes. Commit them first:"
    echo ""
    git status -s
    echo ""
    read -p "Do you want to commit all changes now? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        read -p "Enter commit message: " commit_msg
        git add .
        git commit -m "$commit_msg"
        git push origin main
        echo "✅ Changes committed and pushed"
    else
        echo "❌ Please commit your changes first"
        exit 1
    fi
fi

echo ""
echo "📋 Deployment Checklist:"
echo ""
echo "1. Backend (Render):"
echo "   - Go to: https://dashboard.render.com/"
echo "   - Create new Web Service"
echo "   - Build Command: pip install -r backend/requirements.txt"
echo "   - Start Command: cd backend && uvicorn main:app --host 0.0.0.0 --port \$PORT"
echo ""
echo "2. Update frontend/.env.production with your Render URL"
echo ""
echo "3. Frontend (Vercel):"
echo "   - Run: vercel"
echo "   - Then: vercel --prod"
echo ""

read -p "Have you deployed the backend to Render? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    read -p "Enter your Render backend URL (e.g., https://your-app.onrender.com): " backend_url
    
    # Update .env.production
    echo "VITE_API_BASE_URL=$backend_url" > frontend/.env.production
    echo "✅ Updated frontend/.env.production"
    
    # Commit the change
    git add frontend/.env.production
    git commit -m "Update production API URL"
    git push origin main
    echo "✅ Committed and pushed changes"
    
    echo ""
    echo "🎯 Now deploying to Vercel..."
    
    # Check if vercel is installed
    if ! command -v vercel &> /dev/null; then
        echo "⚠️  Vercel CLI not found. Installing..."
        npm install -g vercel
    fi
    
    echo ""
    read -p "Deploy to Vercel now? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        vercel --prod
        echo ""
        echo "✅ Deployment complete!"
    else
        echo "Run 'vercel --prod' when ready to deploy"
    fi
else
    echo ""
    echo "📝 Next steps:"
    echo "1. Deploy backend to Render first"
    echo "2. Run this script again"
fi

echo ""
echo "📚 For detailed instructions, see DEPLOYMENT_GUIDE.md"
