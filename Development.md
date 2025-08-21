# Deployment Guide

## Environment Setup

### 1. M-Pesa Credentials
Get your credentials from [Safaricom Developer Portal](https://developer.safaricom.co.ke/):
- Consumer Key
- Consumer Secret
- Business Short Code
- Passkey

### 2. Notion Integration (Optional)
1. Go to [Notion Integrations](https://www.notion.so/integrations)
2. Create new integration
3. Get Integration Token
4. Create database and share with integration
5. Copy database ID from URL

## Deployment Options

### Option 1: Render (Recommended for beginners)

#### Backend Deployment:
1. Connect GitHub repository
2. Create new Web Service
3. Build Command: `pip install -r requirements.txt`
4. Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Set environment variables from .env.example

#### Frontend Deployment:
1. Create new Static Site
2. Build Command: `npm install && npm run build`
3. Publish Directory: `build`
4. Set REACT_APP_API_URL to your backend URL

### Option 2: Railway

1. Connect GitHub repository
2. Railway will auto-detect the setup
3. Set environment variables
4. Deploy with one click

### Option 3: VPS (Advanced)

```bash
# Clone repository
git clone your-repo-url
cd qr-payment-system

# Setup environment
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

# Edit environment files with your credentials
nano backend/.env
nano frontend/.env

# Build and run
docker-compose up -d
```
