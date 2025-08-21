# backend/app/services/notion.py
"""
Notion Service - Logs payment data to Notion database

FUNCTION OVERVIEW:
- Automatically logs successful payments to a Notion database
- Creates structured records with payment details
- Provides backup/audit trail outside main database
- Enables easy sharing with non-technical team members
- Can be used for analytics and reporting

NOTION DATABASE STRUCTURE:
The Notion database should have these properties:
- Payment ID (Title)
- Phone Number (Phone)
- Amount (Number - Currency)
- Transaction Code (Rich Text)
- Status (Select: Pending, Success, Failed)
- Created At (Date & Time)
- Updated At (Date & Time)

SETUP INSTRUCTIONS:
1. Go to notion.so/integrations
2. Create new integration, get API key
3. Create database in Notion workspace
4. Share database with integration
5. Copy database ID from URL
6. Set NOTION_API_KEY and NOTION_DATABASE_ID in .env
"""

import httpx
from typing import Dict, Any, Optional
from datetime import datetime
from app.models.payment import Payment
from app.config.settings import settings

class NotionService:
    def __init__(self):
        self.api_key = settings.NOTION_API_KEY
        self.database_id = settings.NOTION_DATABASE_ID
        self.base_url = "https://api.notion.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
    
    def is_configured(self) -> bool:
        """Check if Notion integration is configured"""
        return bool(self.api_key and self.database_id)
    
    async def log_payment(self, payment: Payment) -> bool:
        """Log payment to Notion database"""
        if not self.is_configured():
            print("Notion not configured, skipping logging")
            return False
        
        try:
            # Prepare payment data for Notion
            notion_data = {
                "parent": {
                    "database_id": self.database_id
                },
                "properties": {
                    "Payment ID": {
                        "title": [
                            {
                                "text": {
                                    "content": payment.payment_id
                                }
                            }
                        ]
                    },
                    "Phone Number": {
                        "phone_number": payment.phone_number
                    },
                    "Amount": {
                        "number": float(payment.amount)
                    },
                    "Transaction Code": {
                        "rich_text": [
                            {
                                "text": {
                                    "content": payment.transaction_code or "N/A"
                                }
                            }
                        ]
                    },
                    "Status": {
                        "select": {
                            "name": payment.status.capitalize()
                        }
                    },
                    "Created At": {
                        "date": {
                            "start": payment.created_at.isoformat() if payment.created_at else datetime.utcnow().isoformat()
                        }
                    },
                    "Updated At": {
                        "date": {
                            "start": payment.updated_at.isoformat() if payment.updated_at else datetime.utcnow().isoformat()
                        }
                    }
                }
            }
            
            # Send to Notion
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/pages",
                    json=notion_data,
                    headers=self.headers
                )
                
                if response.status_code == 200:
                    print(f"✅ Payment {payment.payment_id} logged to Notion successfully")
                    return True
                else:
                    print(f"❌ Failed to log payment to Notion: {response.status_code} - {response.text}")
                    return False
                    
        except Exception as e:
            print(f"❌ Error logging payment to Notion: {str(e)}")
            return False
    
    async def update_payment_status(self, payment_id: str, status: str, transaction_code: Optional[str] = None) -> bool:
        """Update payment status in Notion (if record exists)"""
        if not self.is_configured():
            return False
        
        try:
            # First, find the page with the payment ID
            page_id = await self._find_payment_page(payment_id)
            
            if not page_id:
                print(f"Payment {payment_id} not found in Notion")
                return False
            
            # Prepare update data
            update_data = {
                "properties": {
                    "Status": {
                        "select": {
                            "name": status.capitalize()
                        }
                    },
                    "Updated At": {
                        "date": {
                            "start": datetime.utcnow().isoformat()
                        }
                    }
                }
            }
            
            # Add transaction code if provided
            if transaction_code:
                update_data["properties"]["Transaction Code"] = {
                    "rich_text": [
                        {
                            "text": {
                                "content": transaction_code
                            }
                        }
                    ]
                }
            
            # Update the page
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.patch(
                    f"{self.base_url}/pages/{page_id}",
                    json=update_data,
                    headers=self.headers
                )
                
                if response.status_code == 200:
                    print(f"✅ Payment {payment_id} updated in Notion")
                    return True
                else:
                    print(f"❌ Failed to update payment in Notion: {response.status_code}")
                    return False
                    
        except Exception as e:
            print(f"❌ Error updating payment in Notion: {str(e)}")
            return False
    
    async def _find_payment_page(self, payment_id: str) -> Optional[str]:
        """Find Notion page by payment ID"""
        try:
            query_data = {
                "filter": {
                    "property": "Payment ID",
                    "title": {
                        "equals": payment_id
                    }
                }
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/databases/{self.database_id}/query",
                    json=query_data,
                    headers=self.headers
                )
                
                if response.status_code == 200:
                    data = response.json()
                    results = data.get("results", [])
                    
                    if results:
                        return results[0]["id"]
                
                return None
                
        except Exception as e:
            print(f"❌ Error finding payment in Notion: {str(e)}")
            return None
    
    async def get_payment_analytics(self) -> Dict[str, Any]:
        """Get payment analytics from Notion database"""
        if not self.is_configured():
            return {"error": "Notion not configured"}
        
        try:
            # Query all successful payments
            query_data = {
                "filter": {
                    "property": "Status",
                    "select": {
                        "equals": "Success"
                    }
                }
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/databases/{self.database_id}/query",
                    json=query_data,
                    headers=self.headers
                )
                
                if response.status_code == 200:
                    data = response.json()
                    results = data.get("results", [])
                    
                    # Calculate basic analytics
                    total_payments = len(results)
                    total_amount = 0
                    
                    for result in results:
                        amount_property = result.get("properties", {}).get("Amount", {})
                        if amount_property.get("number"):
                            total_amount += amount_property["number"]
                    
                    return {
                        "total_successful_payments": total_payments,
                        "total_amount_collected": total_amount,
                        "average_payment": total_amount / total_payments if total_payments > 0 else 0
                    }
                else:
                    return {"error": f"Failed to fetch data: {response.status_code}"}
                    
        except Exception as e:
            print(f"❌ Error getting analytics from Notion: {str(e)}")
            return {"error": str(e)}
    
    async def create_payment_database(self, parent_page_id: str) -> Optional[str]:
        """Helper function to create the payments database in Notion"""
        if not self.is_configured():
            return None
        
        try:
            database_data = {
                "parent": {
                    "type": "page_id",
                    "page_id": parent_page_id
                },
                "title": [
                    {
                        "type": "text",
                        "text": {
                            "content": "QR Payment System - Payments Database"
                        }
                    }
                ],
                "properties": {
                    "Payment ID": {
                        "title": {}
                    },
                    "Phone Number": {
                        "phone_number": {}
                    },
                    "Amount": {
                        "number": {
                            "format": "kenyan_shilling"
                        }
                    },
                    "Transaction Code": {
                        "rich_text": {}
                    },
                    "Status": {
                        "select": {
                            "options": [
                                {
                                    "name": "Pending",
                                    "color": "yellow"
                                },
                                {
                                    "name": "Success", 
                                    "color": "green"
                                },
                                {
                                    "name": "Failed",
                                    "color": "red"
                                }
                            ]
                        }
                    },
                    "Created At": {
                        "date": {}
                    },
                    "Updated At": {
                        "date": {}
                    }
                }
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/databases",
                    json=database_data,
                    headers=self.headers
                )
                
                if response.status_code == 200:
                    database = response.json()
                    database_id = database["id"]
                    print(f"✅ Created Notion database with ID: {database_id}")
                    return database_id
                else:
                    print(f"❌ Failed to create database: {response.status_code} - {response.text}")
                    return None
                    
        except Exception as e:
            print(f"❌ Error creating Notion database: {str(e)}")
            return None
    
    async def get_daily_summary(self, date: Optional[datetime] = None) -> Dict[str, Any]:
        """Get daily payment summary"""
        if not self.is_configured():
            return {"error": "Notion not configured"}
        
        target_date = date or datetime.utcnow()
        start_date = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = target_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        try:
            query_data = {
                "filter": {
                    "and": [
                        {
                            "property": "Status",
                            "select": {
                                "equals": "Success"
                            }
                        },
                        {
                            "property": "Created At",
                            "date": {
                                "on_or_after": start_date.isoformat()
                            }
                        },
                        {
                            "property": "Created At",
                            "date": {
                                "on_or_before": end_date.isoformat()
                            }
                        }
                    ]
                }
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/databases/{self.database_id}/query",
                    json=query_data,
                    headers=self.headers
                )
                
                if response.status_code == 200:
                    data = response.json()
                    results = data.get("results", [])
                    
                    total_payments = len(results)
                    total_amount = sum(
                        result.get("properties", {}).get("Amount", {}).get("number", 0)
                        for result in results
                    )
                    
                    return {
                        "date": target_date.strftime("%Y-%m-%d"),
                        "total_payments": total_payments,
                        "total_amount": total_amount,
                        "average_payment": total_amount / total_payments if total_payments > 0 else 0
                    }
                else:
                    return {"error": f"Failed to fetch daily summary: {response.status_code}"}
                    
        except Exception as e:
            print(f"❌ Error getting daily summary from Notion: {str(e)}")
            return {"error": str(e)}