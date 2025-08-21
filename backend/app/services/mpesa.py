# backend/app/services/mpesa.py
import httpx
import base64
from datetime import datetime
import asyncio
from typing import Dict, Any
from app.config.settings import settings

class MPesaService:
    def __init__(self):
        self.consumer_key = settings.MPESA_CONSUMER_KEY
        self.consumer_secret = settings.MPESA_CONSUMER_SECRET
        self.business_shortcode = settings.MPESA_BUSINESS_SHORT_CODE
        self.passkey = settings.MPESA_PASSKEY
        self.callback_url = settings.MPESA_CALLBACK_URL
        self.environment = settings.MPESA_ENVIRONMENT
        
        # Set API URLs based on environment
        if self.environment == "production":
            self.auth_url = "https://api.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
            self.stk_url = "https://api.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
        else:
            self.auth_url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
            self.stk_url = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
    
    async def get_access_token(self) -> str:
        """Get M-Pesa access token"""
        try:
            # Create basic auth credentials
            credentials = f"{self.consumer_key}:{self.consumer_secret}"
            credentials_b64 = base64.b64encode(credentials.encode()).decode()
            
            headers = {
                "Authorization": f"Basic {credentials_b64}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(self.auth_url, headers=headers)
                response.raise_for_status()
                
                data = response.json()
                return data.get("access_token")
                
        except Exception as e:
            print(f"Error getting M-Pesa access token: {str(e)}")
            raise
    
    def generate_password(self) -> tuple:
        """Generate M-Pesa password and timestamp"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        password_str = f"{self.business_shortcode}{self.passkey}{timestamp}"
        password = base64.b64encode(password_str.encode()).decode()
        return password, timestamp
    
    async def stk_push(self, phone: str, amount: float, reference: str) -> Dict[str, Any]:
        """Initiate STK Push payment"""
        try:
            # Get access token
            access_token = await self.get_access_token()
            
            if not access_token:
                return {"success": False, "message": "Failed to get access token"}
            
            # Generate password and timestamp
            password, timestamp = self.generate_password()
            
            # Prepare STK Push payload
            payload = {
                "BusinessShortCode": self.business_shortcode,
                "Password": password,
                "Timestamp": timestamp,
                "TransactionType": "CustomerPayBillOnline",
                "Amount": int(amount),  # M-Pesa expects integer
                "PartyA": phone,
                "PartyB": self.business_shortcode,
                "PhoneNumber": phone,
                "CallBackURL": self.callback_url,
                "AccountReference": reference,
                "TransactionDesc": f"Payment for order {reference}"
            }
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.stk_url,
                    json=payload,
                    headers=headers
                )
                
                response_data = response.json()
                
                if response.status_code == 200 and response_data.get("ResponseCode") == "0":
                    return {
                        "success": True,
                        "message": "STK push sent successfully",
                        "checkout_request_id": response_data.get("CheckoutRequestID"),
                        "response_code": response_data.get("ResponseCode"),
                        "response_description": response_data.get("ResponseDescription")
                    }
                else:
                    return {
                        "success": False,
                        "message": response_data.get("ResponseDescription", "STK push failed"),
                        "response_code": response_data.get("ResponseCode"),
                        "response_data": response_data
                    }
                    
        except httpx.TimeoutException:
            return {
                "success": False,
                "message": "Request timeout - please try again"
            }
        except Exception as e:
            print(f"Error in STK push: {str(e)}")
            return {
                "success": False,
                "message": "Failed to process payment request"
            }
    
    async def query_stk_status(self, checkout_request_id: str) -> Dict[str, Any]:
        """Query STK Push payment status"""
        try:
            access_token = await self.get_access_token()
            
            if not access_token:
                return {"success": False, "message": "Failed to get access token"}
            
            password, timestamp = self.generate_password()
            
            # Set query URL based on environment
            if self.environment == "production":
                query_url = "https://api.safaricom.co.ke/mpesa/stkpushquery/v1/query"
            else:
                query_url = "https://sandbox.safaricom.co.ke/mpesa/stkpushquery/v1/query"
            
            payload = {
                "BusinessShortCode": self.business_shortcode,
                "Password": password,
                "Timestamp": timestamp,
                "CheckoutRequestID": checkout_request_id
            }
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    query_url,
                    json=payload,
                    headers=headers
                )
                
                response_data = response.json()
                
                return {
                    "success": response.status_code == 200,
                    "data": response_data
                }
                
        except Exception as e:
            print(f"Error querying STK status: {str(e)}")
            return {
                "success": False,
                "message": "Failed to query payment status"
            }

    async def register_c2b_urls(self, confirmation_url: str, validation_url: str) -> Dict[str, Any]:
        """Register C2B URLs for paybill/till payments"""
        try:
            access_token = await self.get_access_token()
            
            if not access_token:
                return {"success": False, "message": "Failed to get access token"}
            
            # Set C2B URL based on environment
            if self.environment == "production":
                c2b_url = "https://api.safaricom.co.ke/mpesa/c2b/v1/registerurl"
            else:
                c2b_url = "https://sandbox.safaricom.co.ke/mpesa/c2b/v1/registerurl"
            
            payload = {
                "BusinessShortCode": self.business_shortcode,
                "ResponseType": "Completed",
                "ConfirmationURL": confirmation_url,
                "ValidationURL": validation_url
            }
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    c2b_url,
                    json=payload,
                    headers=headers
                )
                
                response_data = response.json()
                
                if response.status_code == 200 and response_data.get("ResponseCode") == "0":
                    return {
                        "success": True,
                        "message": "C2B URLs registered successfully",
                        "response_code": response_data.get("ResponseCode"),
                        "response_description": response_data.get("ResponseDescription")
                    }
                else:
                    return {
                        "success": False,
                        "message": response_data.get("ResponseDescription", "Failed to register C2B URLs"),
                        "response_code": response_data.get("ResponseCode"),
                        "response_data": response_data
                    }
                    
        except Exception as e:
            print(f"Error registering C2B URLs: {str(e)}")
            return {
                "success": False,
                "message": "Failed to register C2B URLs"
            }