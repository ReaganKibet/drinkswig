# backend/app/main.py
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os
from typing import Optional
import uuid
import asyncio
from datetime import datetime

from app.models.payment import Payment, PaymentRequest, PaymentStatusResponse
from app.services.mpesa import MPesaService
from app.services.database import DatabaseService
from app.services.notion import NotionService
from app.config.settings import settings
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Starting up...")
    await db_service.init_db()  # Initialize database
    print("✅ Database initialized")
    yield
    print("🛑 Shutting down...")

# Initialize FastAPI app
app = FastAPI(
    title="QR Payment System",
    description="QR Code to M-Pesa Payment System",
    version="0.1.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://drinkswig-1.onrender.com",  # Your frontend URL
        "http://localhost:3000",  # For local development  
        "*"  # Temporarily allow all origins for testing
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
mpesa_service = MPesaService()
db_service = DatabaseService()
notion_service = NotionService()
security = HTTPBearer()

# Authentication dependency
async def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.credentials != settings.API_SECRET_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return credentials



@app.get("/")
async def root():
    return {"message": "QR Payment System API", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}

@app.post("/api/payments/initiate", dependencies=[Depends(verify_api_key)])
async def initiate_payment(payment_request: PaymentRequest):
    """Initiate M-Pesa STK Push payment"""
    try:
        # Generate unique payment ID
        payment_id = str(uuid.uuid4())
        
        # Initiate STK Push FIRST to get checkout_request_id
        stk_response = await mpesa_service.stk_push(
            phone=payment_request.phone,
            amount=payment_request.amount,
            reference=payment_id
        )
        
        # Extract checkout request ID from STK response
        checkout_request_id = stk_response.get("checkout_request_id")
        
        # Create payment record
        payment = Payment(
            payment_id=payment_id,
            phone_number=payment_request.phone,
            amount=payment_request.amount,
            status="pending",
            checkout_request_id=checkout_request_id
        )
        
        # Save to database
        await db_service.create_payment(payment)
        
        if stk_response.get("success"):
            return {
                "payment_id": payment_id,
                "status": "initiated",
                "message": "STK push sent to your phone"
            }
        else:
            # Update payment status to failed
            await db_service.update_payment_status(payment_id, "failed")
            raise HTTPException(status_code=400, detail="Failed to initiate payment")
            
    except Exception as e:
        print(f"Error initiating payment: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/payments/status/{payment_id}")
async def get_payment_status(payment_id: str):
    """Get payment status"""
    try:
        payment = await db_service.get_payment(payment_id)
        if not payment:
            raise HTTPException(status_code=404, detail="Payment not found")
        
        return PaymentStatusResponse(
            payment_id=payment_id,
            status=payment.status,
            amount=payment.amount,
            transaction_code=payment.transaction_code,
            created_at=payment.created_at
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting payment status: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/api/payments/callback")
async def mpesa_callback(callback_data: dict, request: Request):
    """Handle M-Pesa callback"""
    try:
        print(f"🔔 CALLBACK RECEIVED: {callback_data}")
        print(f"🔔 CALLBACK FROM IP: {request.client.host if hasattr(request, 'client') else 'unknown'}")
        print(f"🔔 CALLBACK HEADERS: {request.headers if hasattr(request, 'headers') else 'unknown'}")
        
        stk = callback_data.get("Body", {}).get("stkCallback", {}) or {}
        result_code = stk.get("ResultCode")
        checkout_request_id = stk.get("CheckoutRequestID")
        
        print(f"📱 STK Data: result_code={result_code}, checkout_request_id={checkout_request_id}")

        try:
            result_code_int = int(result_code)
        except (TypeError, ValueError):
            result_code_int = -1

        if not checkout_request_id:
            print("❌ Missing checkout_request_id")
            return {"status": "ignored", "reason": "missing checkout_request_id"}

        payment = await db_service.get_payment_by_checkout_request_id(checkout_request_id)
        if not payment:
            print(f"❌ Payment not found for checkout_request_id: {checkout_request_id}")
            return {"status": "ignored", "reason": "payment not found"}

        print(f"✅ Found payment: {payment.payment_id}, current status: {payment.status}")

        if result_code_int == 0:
            transaction_code = None
            for item in (stk.get("CallbackMetadata", {}) or {}).get("Item", []) or []:
                if item.get("Name") == "MpesaReceiptNumber":
                    transaction_code = item.get("Value")
                    break

            if transaction_code:
                print(f"💰 Updating to success with transaction: {transaction_code}")
                await db_service.update_payment_success(payment.payment_id, transaction_code)
            else:
                print("✅ Updating to success (no transaction code)")
                await db_service.update_payment_status(payment.payment_id, "success")

            try:
                await notion_service.log_payment(payment)
                print("📝 Logged to Notion")
            except Exception as e:
                print(f"⚠️ Notion logging failed: {e}")
        else:
            print(f"❌ Payment failed with result_code: {result_code_int}")
            await db_service.update_payment_status(payment.payment_id, "failed")

        print(f"✅ Callback processed successfully")
        return {"status": "callback processed"}
    except Exception as e:
        print(f"💥 Error processing callback: {str(e)}")
        return {"status": "error", "message": str(e)}

@app.post("/api/payments/c2b/confirmation")
async def c2b_confirmation(callback_data: dict):
    """Handle C2B confirmation callbacks (paybill/till payments)"""
    try:
        print(f"🔔 C2B CONFIRMATION RECEIVED: {callback_data}")
        
        # Extract C2B data
        transaction_type = callback_data.get("TransactionType")
        trans_id = callback_data.get("TransID")
        trans_time = callback_data.get("TransTime")
        trans_amount = callback_data.get("TransAmount")
        business_shortcode = callback_data.get("BusinessShortCode")
        bill_reference = callback_data.get("BillReferenceNumber")
        invoice_number = callback_data.get("InvoiceNumber")
        org_account_balance = callback_data.get("OrgAccountBalance")
        msisdn = callback_data.get("MSISDN")
        first_name = callback_data.get("FirstName")
        middle_name = callback_data.get("MiddleName")
        last_name = callback_data.get("LastName")
        
        print(f"📱 C2B Data: type={transaction_type}, amount={trans_amount}, phone={msisdn}")
        
        # Create payment record for C2B payment
        payment_id = str(uuid.uuid4())
        payment = Payment(
            payment_id=payment_id,
            phone_number=msisdn,
            amount=float(trans_amount),
            status="success",
            transaction_code=trans_id,
            created_at=datetime.utcnow()
        )
        
        await db_service.create_payment(payment)
        
        # Log to Notion
        try:
            await notion_service.log_payment(payment)
            print("📝 C2B payment logged to Notion")
        except Exception as e:
            print(f"⚠️ Notion logging failed: {e}")
        
        print(f"✅ C2B confirmation processed successfully")
        return {
            "ResultCode": 0,
            "ResultDesc": "Success"
        }
        
    except Exception as e:
        print(f"💥 Error processing C2B confirmation: {str(e)}")
        return {
            "ResultCode": 1,
            "ResultDesc": "Failed"
        }

@app.post("/api/payments/c2b/validation")
async def c2b_validation(callback_data: dict):
    """Handle C2B validation callbacks (paybill/till payments)"""
    try:
        print(f"🔔 C2B VALIDATION RECEIVED: {callback_data}")
        
        # Extract C2B data
        transaction_type = callback_data.get("TransactionType")
        trans_amount = callback_data.get("TransAmount")
        business_shortcode = callback_data.get("BusinessShortCode")
        bill_reference = callback_data.get("BillReferenceNumber")
        invoice_number = callback_data.get("InvoiceNumber")
        msisdn = callback_data.get("MSISDN")
        first_name = callback_data.get("FirstName")
        middle_name = callback_data.get("MiddleName")
        last_name = callback_data.get("LastName")
        
        print(f"📱 C2B Validation: type={transaction_type}, amount={trans_amount}, phone={msisdn}")
        
        # For validation, you can add business logic here
        # For now, we'll accept all validations
        print(f"✅ C2B validation accepted")
        return {
            "ResultCode": 0,
            "ResultDesc": "Accept"
        }
        
    except Exception as e:
        print(f"💥 Error processing C2B validation: {str(e)}")
        return {
            "ResultCode": 1,
            "ResultDesc": "Reject"
        }
        
@app.get("/api/payments/history")
async def get_payment_history(
    limit: int = 50, 
    offset: int = 0,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get payment history (admin endpoint)"""
    if credentials.credentials != settings.API_SECRET_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    try:
        payments = await db_service.get_payments(limit=limit, offset=offset)
        return {"payments": payments, "total": len(payments)}
    except Exception as e:
        print(f"Error getting payment history: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/payments/register-c2b", dependencies=[Depends(verify_api_key)])
async def register_c2b_urls():
    """Register C2B URLs for paybill/till payments"""
    try:
        # Use your ngrok URL for callbacks
        confirmation_url = "https://c2730c853c16.ngrok-free.app/api/payments/c2b/confirmation"
        validation_url = "https://c2730c853c16.ngrok-free.app/api/payments/c2b/validation"
        
        result = await mpesa_service.register_c2b_urls(confirmation_url, validation_url)
        
        if result.get("success"):
            return {
                "success": True,
                "message": "C2B URLs registered successfully",
                "confirmation_url": confirmation_url,
                "validation_url": validation_url
            }
        else:
            raise HTTPException(status_code=400, detail=result.get("message", "Failed to register C2B URLs"))
            
    except Exception as e:
        print(f"Error registering C2B URLs: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
