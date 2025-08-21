# backend/app/services/database.py
import aiosqlite
import asyncio
from typing import List, Optional
from datetime import datetime
from app.models.payment import Payment
from app.config.settings import settings

class DatabaseService:
    def __init__(self):
        self.db_path = settings.DATABASE_URL.replace("sqlite:///", "")
    
    async def init_db(self):
        """Initialize database tables"""
        async with aiosqlite.connect(self.db_path) as db:
            # Create payments table with all columns
            await db.execute("""
                CREATE TABLE IF NOT EXISTS payments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    payment_id VARCHAR(50) UNIQUE NOT NULL,
                    phone_number VARCHAR(15) NOT NULL,
                    amount DECIMAL(10,2) NOT NULL,
                    status VARCHAR(20) DEFAULT 'pending',
                    transaction_code VARCHAR(50),
                    checkout_request_id VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Check if checkout_request_id column exists, and add it if missing
            try:
                await db.execute("SELECT checkout_request_id FROM payments LIMIT 1")
            except aiosqlite.OperationalError:
                # Column doesn't exist, add it
                await db.execute("ALTER TABLE payments ADD COLUMN checkout_request_id VARCHAR(100)")
            
            # Create indexes for faster lookups
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_payment_id ON payments(payment_id)
            """)
            
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_checkout_request_id ON payments(checkout_request_id)
            """)
            
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_phone_amount ON payments(phone_number, amount)
            """)
            
            await db.commit()
    
    async def create_payment(self, payment: Payment) -> bool:
            """Create a new payment record"""
            try:
                async with aiosqlite.connect(self.db_path) as db:
                    await db.execute("""
                        INSERT INTO payments (payment_id, phone_number, amount, status, checkout_request_id, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        payment.payment_id,
                        payment.phone_number,
                        payment.amount,
                        payment.status,
                        payment.checkout_request_id,
                        datetime.utcnow(),
                        datetime.utcnow()
                    ))
                    await db.commit()
                    return True
            except Exception as e:
                print(f"Error creating payment: {str(e)}")
                return False
        

    async def get_payment(self, payment_id: str) -> Optional[Payment]:
        """Get payment by payment_id"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute("""
                    SELECT * FROM payments WHERE payment_id = ?
                """, (payment_id,))
                
                row = await cursor.fetchone()
                
                if row:
                    return Payment(
                        id=row['id'],
                        payment_id=row['payment_id'],
                        phone_number=row['phone_number'],
                        amount=row['amount'],
                        status=row['status'],
                        transaction_code=row['transaction_code'],
                        created_at=row['created_at'],
                        updated_at=row['updated_at']
                    )
                return None
        except Exception as e:
            print(f"Error getting payment: {str(e)}")
            return None
    
    async def update_payment_status(self, payment_id: str, status: str) -> bool:
        """Update payment status"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    UPDATE payments 
                    SET status = ?, updated_at = ?
                    WHERE payment_id = ?
                """, (status, datetime.utcnow(), payment_id))
                await db.commit()
                return True
        except Exception as e:
            print(f"Error updating payment status: {str(e)}")
            return False
    
    async def update_payment_success(self, payment_id: str, transaction_code: str) -> bool:
        """Update payment with successful transaction details"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    UPDATE payments 
                    SET status = 'success', transaction_code = ?, updated_at = ?
                    WHERE payment_id = ?
                """, (transaction_code, datetime.utcnow(), payment_id))
                await db.commit()
                return True
        except Exception as e:
            print(f"Error updating payment success: {str(e)}")
            return False
    
    async def find_recent_payment(self, phone_number: str, amount: float) -> Optional[Payment]:
        """Find most recent pending payment for phone and amount"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute("""
                    SELECT * FROM payments 
                    WHERE phone_number = ? AND amount = ? AND status = 'pending'
                    ORDER BY created_at DESC
                    LIMIT 1
                """, (phone_number, amount))
                
                row = await cursor.fetchone()
                
                if row:
                    return Payment(
                        id=row['id'],
                        payment_id=row['payment_id'],
                        phone_number=row['phone_number'],
                        amount=row['amount'],
                        status=row['status'],
                        transaction_code=row['transaction_code'],
                        created_at=row['created_at'],
                        updated_at=row['updated_at']
                    )
                return None
        except Exception as e:
            print(f"Error finding recent payment: {str(e)}")
            return None

    async def get_payment_by_checkout_request_id(self, checkout_request_id: str) -> Optional[Payment]:
        """Get payment by checkout request ID"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute("""
                    SELECT * FROM payments 
                    WHERE checkout_request_id = ?
                    LIMIT 1
                """, (checkout_request_id,))
                
                row = await cursor.fetchone()
                
                if row:
                    return Payment(
                        id=row['id'],
                        payment_id=row['payment_id'],
                        phone_number=row['phone_number'],
                        amount=row['amount'],
                        status=row['status'],
                        transaction_code=row['transaction_code'],
                        created_at=row['created_at'],
                        updated_at=row['updated_at']
                    )
                return None
        except Exception as e:
            print(f"Error getting payment by checkout request ID: {str(e)}")
            return None
    
    async def get_payments(self, limit: int = 50, offset: int = 0) -> List[dict]:
        """Get payment history with pagination"""