from fastapi import APIRouter, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from fastapi import Depends
from datetime import datetime
import uuid

from ..models.payment import (
    PaymentRequest, 
    Payment, 
    PaymentStatusResponse,
    MPesaSTKResponse,
    MPesaCallbackData
)
from ..services.mpesa import MPesaService
from ..services.database import DatabaseService
from ..services.notion import NotionService
from ..config.settings import settings

router = APIRouter(prefix="/api/payments", tags=["payments"])
mpesa_service = MPesaService()
db_service = DatabaseService()
notion_service = NotionService()

@router.post("/initiate")
async def initiate_payment(payment_request: PaymentRequest):
    payment_id = str(uuid.uuid4())
    stk = await mpesa_service.stk_push(payment_request.phone, payment_request.amount, payment_id)
    checkout_request_id = stk.get("checkout_request_id")
    payment = Payment(payment_id=payment_id, phone_number=payment_request.phone, amount=payment_request.amount, status="pending", checkout_request_id=checkout_request_id)
    await db_service.create_payment(payment)
    if not stk.get("success"):
        await db_service.update_payment_status(payment_id, "failed")
        raise HTTPException(status_code=400, detail="Failed to initiate payment")
    return {"payment_id": payment_id, "status": "initiated"}

@router.get("/status/{payment_id}")
async def get_payment_status(payment_id: str):
    p = await db_service.get_payment(payment_id)
    if not p: raise HTTPException(status_code=404, detail="Payment not found")
    return PaymentStatusResponse(payment_id=p.payment_id, status=p.status, amount=p.amount, transaction_code=p.transaction_code, created_at=p.created_at)

@router.post("/callback")
async def mpesa_callback(callback_data: dict):
    """Handle M-Pesa callback"""
    try:
        stk = callback_data.get("Body", {}).get("stkCallback", {}) or {}
        result_code = stk.get("ResultCode")
        checkout_request_id = stk.get("CheckoutRequestID")

        try:
            result_code_int = int(result_code)
        except (TypeError, ValueError):
            result_code_int = -1

        if not checkout_request_id:
            return {"status": "ignored", "reason": "missing checkout_request_id"}

        payment = await db_service.get_payment_by_checkout_request_id(checkout_request_id)
        if not payment:
            return {"status": "ignored", "reason": "payment not found"}

        if result_code_int == 0:
            transaction_code = None
            for item in (stk.get("CallbackMetadata", {}) or {}).get("Item", []) or []:
                if item.get("Name") == "MpesaReceiptNumber":
                    transaction_code = item.get("Value")
                    break

            if transaction_code:
                await db_service.update_payment_success(payment.payment_id, transaction_code)
            else:
                await db_service.update_payment_status(payment.payment_id, "success")

            try:
                await notion_service.log_payment(payment)
            except Exception:
                pass
        else:
            await db_service.update_payment_status(payment.payment_id, "failed")

        return {"status": "callback processed"}
    except Exception as e:
        print(f"Error processing callback: {str(e)}")
        return {"status": "error", "message": str(e)}

@router.post("/timeout")
async def mpesa_timeout():
    """Handle M-Pesa timeout callbacks"""
    return {"status": "received"}