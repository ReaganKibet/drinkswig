# backend/app/models/payment.py
from pydantic import BaseModel, validator
from typing import Optional
from datetime import datetime
import re

class PaymentRequest(BaseModel):
    """Request model for initiating payment"""
    phone: str
    amount: float
    
    @validator('phone')
    def validate_phone(cls, v):
        # Ensure phone is in 254XXXXXXXXX format
        phone_pattern = r'^254[0-9]{9}$'
        if not re.match(phone_pattern, v):
            raise ValueError('Phone number must be in format 254XXXXXXXXX')
        return v
    
    @validator('amount')
    def validate_amount(cls, v):
        if v < 1:
            raise ValueError('Amount must be at least KES 1')
        if v > 100000:
            raise ValueError('Amount cannot exceed KES 100,000')
        return round(v, 2)

class Payment(BaseModel):
    """Payment model for database storage"""
    id: Optional[int] = None
    payment_id: str
    phone_number: str
    amount: float
    status: str = "pending"  # pending, success, failed
    transaction_code: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    checkout_request_id: Optional[str] = None
    
    class Config:
        from_attributes = True

class PaymentStatusResponse(BaseModel):
    """Response model for payment status"""
    payment_id: str
    status: str
    amount: float
    transaction_code: Optional[str] = None
    created_at: Optional[datetime] = None

class MPesaSTKResponse(BaseModel):
    """M-Pesa STK Push response model"""
    success: bool
    message: str
    checkout_request_id: Optional[str] = None
    response_code: Optional[str] = None
    response_description: Optional[str] = None

class MPesaCallbackData(BaseModel):
    """M-Pesa callback data model"""
    result_code: int
    result_desc: str
    checkout_request_id: str
    transaction_code: Optional[str] = None
    phone_number: Optional[str] = None
    amount: Optional[float] = None