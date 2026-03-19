# 🏗️ Deployment Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         PRODUCTION                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────┐                  ┌──────────────────┐   │
│  │                  │                  │                  │   │
│  │   Vercel CDN     │                  │   Render Cloud   │   │
│  │   (Frontend)     │◄────────────────►│   (Backend)      │   │
│  │                  │   HTTPS/REST     │                  │   │
│  │  React + Vite    │                  │  FastAPI + Uvicorn│  │
│  │               