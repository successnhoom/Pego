# Authentication System for Pego
import os
import jwt
import httpx
import random
import string
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from authlib.integrations.starlette_client import OAuth
from passlib.context import CryptContext
from motor.motor_asyncio import AsyncIOMotorDatabase

from models import User, UserLogin, UserRegistration, PhoneOTP, AuthSession, CreditTransaction

# JWT Configuration
JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'pego_secret_key')
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24 * 7  # 7 days

# Google OAuth Configuration
oauth = OAuth()

def configure_oauth():
    oauth.register(
        name='google',
        client_id=os.environ.get('GOOGLE_CLIENT_ID'),
        client_secret=os.environ.get('GOOGLE_CLIENT_SECRET'),
        server_metadata_url='https://accounts.google.com/.well-known/openid_configuration',
        client_kwargs={
            'scope': 'openid email profile'
        }
    )

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Security
security = HTTPBearer()

class AuthManager:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        configure_oauth()

    # JWT Token Management
    def create_access_token(self, data: dict) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        return encoded_jwt

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token and return payload"""
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )

    # Google OAuth
    async def verify_google_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify Google OAuth token and get user info"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://oauth2.googleapis.com/tokeninfo?id_token={token}"
                )
                if response.status_code == 200:
                    return response.json()
                return None
        except Exception as e:
            print(f"Google token verification error: {e}")
            return None

    async def login_with_google(self, google_token: str) -> Dict[str, Any]:
        """Login or register user with Google OAuth"""
        # Verify Google token
        google_user = await self.verify_google_token(google_token)
        if not google_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid Google token"
            )

        email = google_user.get('email')
        google_id = google_user.get('sub')
        name = google_user.get('name', email.split('@')[0])
        picture = google_user.get('picture')

        # Check if user exists
        user_doc = await self.db.users.find_one({
            "$or": [
                {"email": email},
                {"google_id": google_id}
            ]
        })

        if user_doc:
            # Update existing user
            await self.db.users.update_one(
                {"id": user_doc["id"]},
                {
                    "$set": {
                        "google_id": google_id,
                        "last_active": datetime.utcnow(),
                        "avatar_url": picture if not user_doc.get("avatar_url") else user_doc.get("avatar_url")
                    }
                }
            )
            user = User(**user_doc)
        else:
            # Create new user
            username = await self.generate_unique_username(name)
            user = User(
                username=username,
                display_name=name,
                email=email,
                google_id=google_id,
                avatar_url=picture,
                credits=0  # New users start with 0 credits
            )
            await self.db.users.insert_one(user.dict())

        # Create session
        session_token = self.create_access_token({"user_id": user.id, "email": email})
        
        return {
            "user": user.dict(),
            "access_token": session_token,
            "token_type": "bearer"
        }

    # Phone OTP System
    def generate_otp(self) -> str:
        """Generate 6-digit OTP"""
        return ''.join(random.choices(string.digits, k=6))

    async def send_otp(self, phone: str) -> Dict[str, str]:
        """Send OTP to phone number"""
        # Clean phone number
        phone = phone.replace('+', '').replace('-', '').replace(' ', '')
        
        # Generate OTP
        otp_code = self.generate_otp()
        expires_at = datetime.utcnow() + timedelta(minutes=5)  # 5 minutes expiry

        # Store OTP in database
        otp_record = PhoneOTP(
            phone=phone,
            otp_code=otp_code,
            expires_at=expires_at
        )
        await self.db.phone_otps.insert_one(otp_record.dict())

        # TODO: Integrate with SMS service (Twilio, etc.)
        # For now, return OTP in response for testing
        print(f"OTP for {phone}: {otp_code}")  # Development only
        
        return {
            "message": "OTP sent successfully",
            "phone": phone,
            "otp": otp_code  # Remove this in production!
        }

    async def verify_otp(self, phone: str, otp_code: str) -> bool:
        """Verify OTP code"""
        # Find valid OTP
        otp_record = await self.db.phone_otps.find_one({
            "phone": phone,
            "otp_code": otp_code,
            "is_used": False,
            "expires_at": {"$gt": datetime.utcnow()}
        })

        if not otp_record:
            return False

        # Mark OTP as used
        await self.db.phone_otps.update_one(
            {"id": otp_record["id"]},
            {"$set": {"is_used": True}}
        )
        
        return True

    async def login_with_phone(self, phone: str, otp_code: str) -> Dict[str, Any]:
        """Login or register user with phone OTP"""
        # Verify OTP
        if not await self.verify_otp(phone, otp_code):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired OTP"
            )

        # Check if user exists
        user_doc = await self.db.users.find_one({"phone": phone})

        if user_doc:
            # Update existing user
            await self.db.users.update_one(
                {"id": user_doc["id"]},
                {"$set": {"last_active": datetime.utcnow()}}
            )
            user = User(**user_doc)
        else:
            # Create new user with phone
            username = await self.generate_unique_username(f"user{phone[-4:]}")
            user = User(
                username=username,
                display_name=f"ผู้ใช้ {phone[-4:]}",
                phone=phone,
                credits=0  # New users start with 0 credits
            )
            await self.db.users.insert_one(user.dict())

        # Create session
        session_token = self.create_access_token({"user_id": user.id, "phone": phone})
        
        return {
            "user": user.dict(),
            "access_token": session_token,
            "token_type": "bearer"
        }

    # User Management
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        user_doc = await self.db.users.find_one({"id": user_id})
        if user_doc:
            return User(**user_doc)
        return None

    async def generate_unique_username(self, base_name: str) -> str:
        """Generate unique username"""
        # Clean base name
        base_username = ''.join(c for c in base_name.lower() if c.isalnum())
        if not base_username:
            base_username = "user"
        
        # Check if username exists
        counter = 0
        username = base_username
        
        while True:
            existing_user = await self.db.users.find_one({"username": username})
            if not existing_user:
                break
            counter += 1
            username = f"{base_username}{counter}"
            
        return username

    async def update_user_profile(self, user_id: str, profile_data: Dict[str, Any]) -> User:
        """Update user profile"""
        # Validate username uniqueness if changed
        if 'username' in profile_data:
            existing_user = await self.db.users.find_one({
                "username": profile_data['username'],
                "id": {"$ne": user_id}
            })
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already exists"
                )

        # Update user
        await self.db.users.update_one(
            {"id": user_id},
            {
                "$set": {
                    **profile_data,
                    "updated_at": datetime.utcnow()
                }
            }
        )

        # Return updated user
        user_doc = await self.db.users.find_one({"id": user_id})
        return User(**user_doc)

    # Credit Management
    async def add_credits(self, user_id: str, amount: int, transaction_type: str, 
                         description: str, payment_session_id: Optional[str] = None) -> int:
        """Add credits to user account"""
        # Update user credits
        result = await self.db.users.update_one(
            {"id": user_id},
            {"$inc": {"credits": amount}}
        )
        
        if result.modified_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Record transaction
        transaction = CreditTransaction(
            user_id=user_id,
            amount=amount,
            transaction_type=transaction_type,
            description=description,
            payment_session_id=payment_session_id
        )
        await self.db.credit_transactions.insert_one(transaction.dict())

        # Get updated credits
        user_doc = await self.db.users.find_one({"id": user_id})
        return user_doc["credits"]

    async def spend_credits(self, user_id: str, amount: int, description: str, 
                           video_id: Optional[str] = None) -> int:
        """Spend credits from user account"""
        # Check if user has enough credits
        user_doc = await self.db.users.find_one({"id": user_id})
        if not user_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        if user_doc["credits"] < amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient credits. You have {user_doc['credits']} credits, need {amount}"
            )

        # Deduct credits
        await self.db.users.update_one(
            {"id": user_id},
            {"$inc": {"credits": -amount}}
        )

        # Record transaction
        transaction = CreditTransaction(
            user_id=user_id,
            amount=-amount,  # Negative for spending
            transaction_type="spend",
            description=description,
            video_id=video_id
        )
        await self.db.credit_transactions.insert_one(transaction.dict())

        return user_doc["credits"] - amount

    async def get_user_credits(self, user_id: str) -> int:
        """Get user's current credits"""
        user_doc = await self.db.users.find_one({"id": user_id})
        if not user_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return user_doc["credits"]


# Dependency to get current user
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncIOMotorDatabase = Depends(lambda: None)  # Will be injected
) -> User:
    """Dependency to get current authenticated user"""
    try:
        # This will be replaced with proper db injection in main server
        from server import get_database
        db = get_database()
        
        auth_manager = AuthManager(db)
        payload = auth_manager.verify_token(credentials.credentials)
        user_id = payload.get("user_id")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )
        
        user = await auth_manager.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        return user
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )

# Optional dependency for routes that work with or without auth
async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[User]:
    """Optional dependency to get current user if authenticated"""
    if not credentials:
        return None
    
    try:
        return await get_current_user(credentials)
    except:
        return None