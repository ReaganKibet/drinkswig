from pydantic_settings import BaseSettings
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "sqlite:///./payments.db"
    
    # M-Pesa Configuration
    MPESA_CONSUMER_KEY: str
    MPESA_CONSUMER_SECRET: str
    MPESA_BUSINESS_SHORT_CODE: str
    MPESA_PASSKEY: str
    MPESA_CALLBACK_URL: str
    MPESA_ENVIRONMENT: str = "sandbox"
    
    # Notion Integration
    NOTION_API_KEY: Optional[str] = None
    NOTION_DATABASE_ID: Optional[str] = None
    
    # Security
    API_SECRET_KEY: str
    FRONTEND_URL: str = "http://localhost:3000"
    
    # WhatsApp
    WHATSAPP_PHONE: str
    WHATSAPP_MESSAGE_TEMPLATE: str = "Hi, I've just paid for the kombucha order. Here are my details..."
    
    class Config:
        env_file = ".env"

settings = Settings()


