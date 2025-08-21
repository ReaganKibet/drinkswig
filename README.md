# QR Payment System

A QR code to M-Pesa payment system with WhatsApp integration.

## Quick Start

### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your actual credentials
uvicorn app.main:app --reload
```

### Frontend Setup
```bash
cd frontend
npm install
cp .env.example .env
# Edit .env with your API URL
npm start
```

### Docker Setup
```bash
docker-compose up --build
```

## Environment Setup

1. **M-Pesa Credentials**: Get from Safaricom Developer Portal
2. **Notion Integration**: Create integration at notion.so/integrations
3. **API Keys**: Generate secure random keys for production

## API Endpoints

- `POST /api/payments/initiate` - Start payment
- `GET /api/payments/status/{id}` - Check payment status  
- `POST /api/payments/callback` - M-Pesa callback
- `GET /api/payments/history` - Payment history (admin)

## Deployment

### Render
1. Connect your GitHub repo
2. Set environment variables
3. Deploy backend as Web Service
4. Deploy frontend as Static Site

### Railway
1. Connect GitHub repo
2. Set environment variables
3. Deploy with one click

## Security Notes

- Change all default API keys
- Use HTTPS in production
- Validate all inputs
- Rate limit API endpoints