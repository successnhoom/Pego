from fastapi import FastAPI, APIRouter, File, UploadFile, HTTPException, Request, Form, status, Depends
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
import uuid
from datetime import datetime, timedelta
import asyncio
import aiofiles
import shutil
import json

# Models and Authentication
from models import Video, User, VideoInteraction, Competition, AlgorithmScore, AdminUser
from auth import AuthManager, get_current_user, get_current_user_optional
from algorithm import VideoRecommendationEngine
from admin_routes import admin_router

# Emergent integrations for payments
from emergentintegrations.payments.stripe.checkout import StripeCheckout, CheckoutSessionResponse, CheckoutStatusResponse, CheckoutSessionRequest

# PromptPay imports
from pypromptpay import qr_code as pp_qrcode
import qrcode
import base64
from io import BytesIO

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
db_name = os.environ.get('DB_NAME', 'pego_database')
client = AsyncIOMotorClient(mongo_url)
db = client[db_name]

# Initialize AuthManager
auth_manager = AuthManager(db)

# Helper function to get database (for dependencies)
def get_database():
    return db

# Create upload directories
UPLOAD_DIR = ROOT_DIR / "uploads" / "videos"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Create the main app
app = FastAPI()

# Add session middleware for OAuth
app.add_middleware(
    SessionMiddleware, 
    secret_key=os.environ.get('SESSION_SECRET_KEY', 'pego_session_secret')
)

api_router = APIRouter(prefix="/api")

# Initialize Algorithm Engine
algorithm_engine = None

async def get_algorithm_engine():
    global algorithm_engine
    if not algorithm_engine:
        algorithm_engine = VideoRecommendationEngine(db)
    return algorithm_engine

# Stripe setup
stripe_api_key = os.environ.get('STRIPE_API_KEY')
stripe_checkout = None

# PromptPay setup
promptpay_id = os.environ.get('PROMPTPAY_ID', '0123456789')  # Default test ID

# Models
class VideoUpload(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    filename: str
    file_path: str
    title: str
    description: Optional[str] = ""
    user_id: str
    file_size: int
    duration: Optional[float] = None
    upload_date: datetime = Field(default_factory=datetime.utcnow)
    view_count: int = 0
    competition_round: str
    is_paid: bool = False
    payment_session_id: Optional[str] = None

class VideoCreate(BaseModel):
    title: str
    description: Optional[str] = ""
    user_id: str

class PaymentMethodRequest(BaseModel):
    video_id: str
    payment_method: str  # "stripe" or "promptpay"
    user_id: str

class VideoView(BaseModel):
    video_id: str
    viewer_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class PaymentSession(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    user_id: str
    video_id: Optional[str] = None
    amount: float
    currency: str
    status: str
    payment_method: str  # "stripe" or "promptpay"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class PromptPaySession(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    qr_code_data: str
    qr_code_image: str  # Base64 encoded image
    user_id: str
    video_id: Optional[str] = None
    amount: float
    currency: str = "THB"
    status: str = "pending"  # pending, paid, expired
    expires_at: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)

class CompetitionRound(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    start_date: datetime
    end_date: datetime
    total_revenue: float = 0.0
    total_videos: int = 0
    prize_pool: float = 0.0
    is_active: bool = True
    winners: List[Dict] = []

# Helper functions
def serialize_doc(doc):
    """Convert MongoDB document to JSON-serializable format"""
    if doc is None:
        return None
    if isinstance(doc, list):
        return [serialize_doc(item) for item in doc]
    if isinstance(doc, dict):
        # Remove MongoDB's _id field and convert ObjectId to string if present
        result = {}
        for key, value in doc.items():
            if key == '_id':
                continue  # Skip MongoDB's _id field
            if hasattr(value, '__dict__'):
                result[key] = serialize_doc(value.__dict__)
            elif isinstance(value, (list, dict)):
                result[key] = serialize_doc(value)
            else:
                result[key] = value
        return result
    return doc

async def get_current_competition_round():
    """Get or create the current active competition round"""
    now = datetime.utcnow()
    current_round = await db.competition_rounds.find_one({
        "is_active": True,
        "start_date": {"$lte": now},
        "end_date": {"$gte": now}
    })
    
    if not current_round:
        # Create new round (7 days)
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=7)
        
        round_data = CompetitionRound(
            start_date=start_date,
            end_date=end_date
        )
        result = await db.competition_rounds.insert_one(round_data.dict())
        return round_data.id
    
    return current_round["id"]

async def init_stripe():
    global stripe_checkout
    if stripe_api_key and not stripe_checkout:
        webhook_url = f"{os.environ.get('FRONTEND_URL', 'http://localhost:3000')}/api/webhook/stripe"
        stripe_checkout = StripeCheckout(api_key=stripe_api_key, webhook_url=webhook_url)

def calculate_crc16(payload: str) -> str:
    """Calculate CRC16 checksum for PromptPay QR"""
    crc = 0xFFFF
    for char in payload:
        crc ^= (ord(char) << 8)
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ 0x1021
            else:
                crc <<= 1
            crc &= 0xFFFF
    return format(crc, '04X')

def generate_promptpay_qr(promptpay_id: str, amount: float) -> dict:
    """Generate PromptPay QR code data and image using EMV format"""
    try:
        # Build EMV QR payload
        payload_parts = [
            '000201',  # Payload format indicator
            '010212',  # Version (12 = dynamic)
        ]
        
        # Merchant Account Information (PromptPay)
        merchant_info = '0016A000000677010111'  # PromptPay AID
        
        # Add payee ID (phone number or ID)
        if len(promptpay_id) == 13:  # National ID
            payee_data = f'0213{promptpay_id}'
        else:  # Phone number (remove leading 0 if exists)
            phone = promptpay_id.lstrip('0')
            payee_data = f'01{len(phone):02d}{phone}'
        
        merchant_account = merchant_info + payee_data
        payload_parts.append(f'29{len(merchant_account):02d}{merchant_account}')
        
        # Currency and country
        payload_parts.append('5303764')  # THB currency code
        payload_parts.append('5802TH')  # Thailand country code
        
        # Transaction amount
        if amount > 0:
            amount_str = f'{amount:.2f}'
            payload_parts.append(f'54{len(amount_str):02d}{amount_str}')
        
        # CRC placeholder
        payload_parts.append('6304')
        
        # Calculate CRC
        payload_without_crc = ''.join(payload_parts)
        crc = calculate_crc16(payload_without_crc)
        
        # Final payload
        qr_data = payload_without_crc + crc
        
        # Create QR code image
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)

        # Generate image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
        
        return {
            "qr_data": qr_data,
            "qr_image": f"data:image/png;base64,{img_base64}"
        }
        
    except Exception as e:
        logger.error(f"PromptPay QR generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate PromptPay QR: {str(e)}")

# Routes
@api_router.get("/")
async def root():
    return {"message": "Pego Video Contest Platform API"}

@api_router.post("/upload/initiate")
async def initiate_upload(request: Request, current_user: User = Depends(get_current_user)):
    """Initiate video upload - requires authentication and sufficient credits"""
    try:
        body = await request.json()
        title = body.get("title")
        description = body.get("description", "")
        hashtags = body.get("hashtags", [])
        
        if not title:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Video title is required"
            )
        
        # Check if user has enough credits (30 credits = 1 video)
        user_credits = await auth_manager.get_user_credits(current_user.id)
        required_credits = 30
        
        if user_credits < required_credits:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient credits. You have {user_credits} credits, need {required_credits} credits to upload"
            )
        
        # Get current competition round
        round_id = await get_current_competition_round()
        
        # Create video record (unpaid initially)
        video = Video(
            filename="",
            file_path="",
            title=title,
            description=description,
            hashtags=hashtags,
            user_id=current_user.id,
            file_size=0,
            competition_round=round_id,
            is_paid=False
        )
        
        result = await db.videos.insert_one(video.dict())
        video_id = video.id
        
        return {
            "video_id": video_id,
            "user_credits": user_credits,
            "required_credits": required_credits,
            "message": "Video initiated successfully. Ready for file upload."
        }
        
    except Exception as e:
        logger.error(f"Video initiation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to initiate upload: {str(e)}")

@api_router.post("/payment/create")
async def create_payment_session(payment_request: PaymentMethodRequest):
    """Create payment session based on selected method"""
    try:
        # Verify video exists
        video_doc = await db.videos.find_one({"id": payment_request.video_id})
        if not video_doc:
            raise HTTPException(status_code=404, detail="Video not found")
        
        if video_doc.get("is_paid", False):
            raise HTTPException(status_code=400, detail="Video already paid")
        
        amount = 30.0  # 30 THB
        
        if payment_request.payment_method == "stripe":
            await init_stripe()
            
            if not stripe_checkout:
                raise HTTPException(status_code=500, detail="Stripe not configured")
            
            # Create Stripe checkout session
            host_url = "http://localhost:3000"
            success_url = f"{host_url}/upload/success?session_id={{CHECKOUT_SESSION_ID}}&video_id={payment_request.video_id}"
            cancel_url = f"{host_url}/upload/cancel"
            
            checkout_request = CheckoutSessionRequest(
                amount=amount,
                currency="thb",
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={
                    "video_id": payment_request.video_id,
                    "user_id": payment_request.user_id,
                    "service": "video_upload"
                }
            )
            
            session: CheckoutSessionResponse = await stripe_checkout.create_checkout_session(checkout_request)
            
            # Store payment session
            payment_session = PaymentSession(
                session_id=session.session_id,
                user_id=payment_request.user_id,
                video_id=payment_request.video_id,
                amount=amount,
                currency="thb",
                status="initiated",
                payment_method="stripe"
            )
            
            await db.payment_sessions.insert_one(payment_session.dict())
            
            return {
                "payment_method": "stripe",
                "checkout_url": session.url,
                "session_id": session.session_id
            }
            
        elif payment_request.payment_method == "promptpay":
            # Generate PromptPay QR code
            qr_result = generate_promptpay_qr(promptpay_id, amount)
            
            # Create PromptPay session (expires in 10 minutes)
            expires_at = datetime.utcnow() + timedelta(minutes=10)
            
            promptpay_session = PromptPaySession(
                qr_code_data=qr_result["qr_data"],
                qr_code_image=qr_result["qr_image"],
                user_id=payment_request.user_id,
                video_id=payment_request.video_id,
                amount=amount,
                currency="THB",
                status="pending",
                expires_at=expires_at
            )
            
            result = await db.promptpay_sessions.insert_one(promptpay_session.dict())
            session_id = promptpay_session.id  # Use our custom UUID instead of MongoDB ObjectId
            
            return {
                "payment_method": "promptpay",
                "session_id": session_id,
                "qr_code": qr_result["qr_image"],
                "amount": amount,
                "currency": "THB",
                "expires_at": expires_at.isoformat(),
                "instructions": "Scan the QR code with your banking app to pay 30 THB"
            }
            
        else:
            raise HTTPException(status_code=400, detail="Invalid payment method")
        
    except Exception as e:
        logger.error(f"Payment creation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create payment session: {str(e)}")

@api_router.get("/payment/status/stripe/{session_id}")
async def check_stripe_payment_status(session_id: str):
    """Check Stripe payment status"""
    await init_stripe()
    
    try:
        # Check with Stripe
        status: CheckoutStatusResponse = await stripe_checkout.get_checkout_status(session_id)
        
        # Update local payment session
        await db.payment_sessions.update_one(
            {"session_id": session_id},
            {
                "$set": {
                    "status": status.payment_status,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        # If payment successful, mark video as paid
        if status.payment_status == "paid":
            video_id = status.metadata.get("video_id")
            if video_id:
                await db.videos.update_one(
                    {"id": video_id},
                    {"$set": {"is_paid": True}}
                )
                
                # Update competition round stats
                await db.competition_rounds.update_one(
                    {"id": await get_current_competition_round()},
                    {
                        "$inc": {
                            "total_revenue": 30.0,
                            "total_videos": 1,
                            "prize_pool": 21.0  # 70% of 30 THB
                        }
                    }
                )
        
        return {
            "session_id": session_id,
            "status": status.status,
            "payment_status": status.payment_status,
            "amount": status.amount_total / 100,  # Convert from cents
            "currency": status.currency,
            "payment_method": "stripe"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to check payment status: {str(e)}")

@api_router.get("/payment/status/promptpay/{session_id}")
async def check_promptpay_payment_status(session_id: str):
    """Check PromptPay payment status"""
    try:
        # Get PromptPay session
        promptpay_session = await db.promptpay_sessions.find_one({"id": session_id})
        
        if not promptpay_session:
            raise HTTPException(status_code=404, detail="PromptPay session not found")
        
        # Check if session expired
        if datetime.utcnow() > promptpay_session["expires_at"]:
            await db.promptpay_sessions.update_one(
                {"id": session_id},
                {"$set": {"status": "expired"}}
            )
            return {
                "session_id": session_id,
                "status": "expired",
                "payment_method": "promptpay"
            }
        
        return {
            "session_id": session_id,
            "status": promptpay_session["status"],
            "amount": promptpay_session["amount"],
            "currency": promptpay_session["currency"],
            "expires_at": promptpay_session["expires_at"].isoformat(),
            "payment_method": "promptpay",
            "qr_code": promptpay_session["qr_code_image"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to check PromptPay status: {str(e)}")

@api_router.post("/payment/confirm/promptpay/{session_id}")
async def confirm_promptpay_payment(session_id: str):
    """Manually confirm PromptPay payment (for testing purposes)"""
    try:
        # Get PromptPay session
        promptpay_session = await db.promptpay_sessions.find_one({"id": session_id})
        
        if not promptpay_session:
            raise HTTPException(status_code=404, detail="PromptPay session not found")
        
        if promptpay_session["status"] == "paid":
            raise HTTPException(status_code=400, detail="Payment already confirmed")
        
        # Check if session expired
        if datetime.utcnow() > promptpay_session["expires_at"]:
            await db.promptpay_sessions.update_one(
                {"id": session_id},
                {"$set": {"status": "expired"}}
            )
            raise HTTPException(status_code=400, detail="Payment session expired")
        
        # Mark payment as paid
        await db.promptpay_sessions.update_one(
            {"id": session_id},
            {"$set": {"status": "paid"}}
        )
        
        # Mark video as paid
        video_id = promptpay_session["video_id"]
        if video_id:
            await db.videos.update_one(
                {"id": video_id},
                {"$set": {"is_paid": True}}
            )
            
            # Update competition round stats
            await db.competition_rounds.update_one(
                {"id": await get_current_competition_round()},
                {
                    "$inc": {
                        "total_revenue": 30.0,
                        "total_videos": 1,
                        "prize_pool": 21.0  # 70% of 30 THB
                    }
                }
            )
        
        return {
            "message": "PromptPay payment confirmed successfully",
            "session_id": session_id,
            "video_id": video_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to confirm PromptPay payment: {str(e)}")

# Authentication endpoints
@api_router.post("/auth/google")
async def login_with_google(request: Request):
    """Login with Google OAuth"""
    try:
        body = await request.json()
        google_token = body.get("google_token")
        
        if not google_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Google token is required"
            )

        result = await auth_manager.login_with_google(google_token)
        return result

    except Exception as e:
        logger.error(f"Google OAuth login failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )

@api_router.post("/auth/phone/send-otp")
async def send_phone_otp(request: Request):
    """Send OTP to phone number"""
    try:
        body = await request.json()
        phone = body.get("phone")
        
        if not phone:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Phone number is required"
            )

        result = await auth_manager.send_otp(phone)
        return result

    except Exception as e:
        logger.error(f"Send OTP failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send OTP: {str(e)}"
        )

@api_router.post("/auth/phone/verify")
async def verify_phone_otp(request: Request):
    """Verify phone OTP and login"""
    try:
        body = await request.json()
        phone = body.get("phone")
        otp_code = body.get("otp_code")
        
        if not phone or not otp_code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Phone number and OTP code are required"
            )

        result = await auth_manager.login_with_phone(phone, otp_code)
        return result

    except Exception as e:
        logger.error(f"Phone OTP verification failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OTP verification failed: {str(e)}"
        )

@api_router.get("/auth/me")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return {
        "user": current_user.dict(),
        "message": "User authenticated successfully"
    }

@api_router.put("/auth/profile")
async def update_user_profile(request: Request, current_user: User = Depends(get_current_user)):
    """Update user profile"""
    try:
        body = await request.json()
        
        # Remove sensitive fields that shouldn't be updated
        allowed_fields = ["username", "display_name", "bio", "avatar_url"]
        profile_data = {k: v for k, v in body.items() if k in allowed_fields}
        
        if not profile_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid fields to update"
            )

        updated_user = await auth_manager.update_user_profile(current_user.id, profile_data)
        return {
            "user": updated_user.dict(),
            "message": "Profile updated successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Profile update failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Profile update failed: {str(e)}"
        )

# Credit system endpoints
@api_router.get("/credits/balance")
async def get_credit_balance(current_user: User = Depends(get_current_user)):
    """Get current user's credit balance"""
    credits = await auth_manager.get_user_credits(current_user.id)
    return {
        "credits": credits,
        "user_id": current_user.id
    }

@api_router.post("/credits/topup")
async def create_credit_topup(request: Request, current_user: User = Depends(get_current_user)):
    """Create credit top-up payment session"""
    try:
        body = await request.json()
        amount_thb = body.get("amount", 0)  # Amount in THB
        payment_method = body.get("payment_method", "promptpay")  # "stripe" or "promptpay"
        
        if amount_thb <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Amount must be greater than 0"
            )
        
        credits_to_add = int(amount_thb)  # 1 THB = 1 Credit

        if payment_method == "stripe":
            await init_stripe()
            
            if not stripe_checkout:
                raise HTTPException(status_code=500, detail="Stripe not configured")
            
            # Create Stripe checkout session
            host_url = "http://localhost:3000"
            success_url = f"{host_url}/credits/success?session_id={{CHECKOUT_SESSION_ID}}"
            cancel_url = f"{host_url}/credits/cancel"
            
            checkout_request = CheckoutSessionRequest(
                amount=float(amount_thb),
                currency="thb",
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={
                    "user_id": current_user.id,
                    "credits": str(credits_to_add),
                    "service": "credit_topup"
                }
            )
            
            session: CheckoutSessionResponse = await stripe_checkout.create_checkout_session(checkout_request)
            
            # Store payment session
            payment_session = PaymentSession(
                session_id=session.session_id,
                user_id=current_user.id,
                amount=float(amount_thb),
                currency="thb",
                status="initiated",
                payment_method="stripe"
            )
            
            await db.payment_sessions.insert_one(payment_session.dict())
            
            return {
                "payment_method": "stripe",
                "checkout_url": session.url,
                "session_id": session.session_id,
                "credits": credits_to_add
            }
        
        elif payment_method == "promptpay":
            # Generate PromptPay QR code
            qr_result = generate_promptpay_qr(promptpay_id, amount_thb)
            
            # Create PromptPay session (expires in 10 minutes)
            expires_at = datetime.utcnow() + timedelta(minutes=10)
            
            promptpay_session = PromptPaySession(
                qr_code_data=qr_result["qr_data"],
                qr_code_image=qr_result["qr_image"],
                user_id=current_user.id,
                amount=float(amount_thb),
                currency="THB",
                status="pending",
                expires_at=expires_at
            )
            
            result = await db.promptpay_sessions.insert_one(promptpay_session.dict())
            session_id = promptpay_session.id  # Use our custom UUID instead of MongoDB ObjectId
            
            return {
                "payment_method": "promptpay",
                "session_id": session_id,
                "qr_code": qr_result["qr_image"],
                "amount": amount_thb,
                "credits": credits_to_add,
                "currency": "THB",
                "expires_at": expires_at.isoformat(),
                "instructions": f"Scan QR code to top up {credits_to_add} credits (฿{amount_thb})"
            }
        
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid payment method"
            )
            
    except Exception as e:
        logger.error(f"Credit topup failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create credit topup: {str(e)}"
        )

@api_router.post("/credits/confirm/promptpay/{session_id}")
async def confirm_credit_topup(session_id: str, current_user: User = Depends(get_current_user)):
    """Confirm PromptPay credit top-up payment"""
    try:
        # Get PromptPay session
        promptpay_session = await db.promptpay_sessions.find_one({"id": session_id})
        
        if not promptpay_session:
            raise HTTPException(status_code=404, detail="Payment session not found")
        
        if promptpay_session["user_id"] != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        if promptpay_session["status"] == "paid":
            raise HTTPException(status_code=400, detail="Payment already confirmed")
        
        # Check if session expired
        if datetime.utcnow() > promptpay_session["expires_at"]:
            await db.promptpay_sessions.update_one(
                {"id": session_id},
                {"$set": {"status": "expired"}}
            )
            raise HTTPException(status_code=400, detail="Payment session expired")
        
        # Mark payment as paid
        await db.promptpay_sessions.update_one(
            {"id": session_id},
            {"$set": {"status": "paid"}}
        )
        
        # Add credits to user account
        credits_to_add = int(promptpay_session["amount"])  # 1 THB = 1 Credit
        new_balance = await auth_manager.add_credits(
            current_user.id,
            credits_to_add,
            "topup",
            f"PromptPay top-up ฿{promptpay_session['amount']}",
            session_id
        )
        
        return {
            "message": "Credit top-up confirmed successfully",
            "session_id": session_id,
            "credits_added": credits_to_add,
            "new_balance": new_balance
        }
        
    except Exception as e:
        logger.error(f"Credit topup confirmation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to confirm credit topup: {str(e)}"
        )

@api_router.get("/payment/methods")
async def get_payment_methods():
    """Get available payment methods"""
    methods = []
    
    # Check if Stripe is available
    if stripe_api_key:
        methods.append({
            "id": "stripe",
            "name": "Credit/Debit Card",
            "description": "Pay with Visa, MasterCard, or other cards",
            "icon": "💳",
            "available": True
        })
    
    # PromptPay is always available (using test ID if not configured)
    methods.append({
        "id": "promptpay",
        "name": "PromptPay",
        "description": "Scan QR code with your Thai banking app",
        "icon": "📱",
        "available": True
    })
    
    return {
        "payment_methods": methods,
        "amount": 30.0,
        "currency": "THB"
    }

@api_router.post("/upload/video/{video_id}")
async def upload_video_file(
    video_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """Upload video file and spend credits"""
    try:
        # Verify video belongs to current user
        video_doc = await db.videos.find_one({"id": video_id, "user_id": current_user.id})
        if not video_doc:
            raise HTTPException(status_code=404, detail="Video not found or access denied")
        
        if video_doc.get("is_paid", False):
            raise HTTPException(status_code=400, detail="Video already uploaded")
        
        # Validate file
        if not file.content_type.startswith("video/"):
            raise HTTPException(status_code=400, detail="File must be a video")
        
        file_size = 0
        temp_file_path = None
        
        try:
            # Save file
            file_extension = Path(file.filename).suffix
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            file_path = UPLOAD_DIR / unique_filename
            
            async with aiofiles.open(file_path, 'wb') as f:
                while chunk := await file.read(1024 * 1024):  # 1MB chunks
                    file_size += len(chunk)
                    await f.write(chunk)
                    
                    # Check file size limit (100MB)
                    if file_size > 100 * 1024 * 1024:
                        await f.close()
                        os.remove(file_path)
                        raise HTTPException(status_code=400, detail="File too large (max 100MB)")
            
            # Spend credits (30 credits per video)
            required_credits = 30
            remaining_credits = await auth_manager.spend_credits(
                current_user.id,
                required_credits,
                f"Video upload: {video_doc['title']}",
                video_id
            )
            
            # Update video record
            await db.videos.update_one(
                {"id": video_id},
                {
                    "$set": {
                        "filename": unique_filename,
                        "file_path": str(file_path),
                        "file_size": file_size,
                        "is_paid": True,
                        "upload_date": datetime.utcnow(),
                        "published_at": datetime.utcnow()
                    }
                }
            )
            
            # Update competition round stats
            await db.competition_rounds.update_one(
                {"id": await get_current_competition_round()},
                {
                    "$inc": {
                        "total_revenue": 30.0,
                        "total_videos": 1,
                        "prize_pool": 21.0  # 70% of 30 THB
                    }
                }
            )
            
            return {
                "message": "Video uploaded successfully!",
                "video_id": video_id,
                "filename": unique_filename,
                "file_size": file_size,
                "credits_spent": required_credits,
                "remaining_credits": remaining_credits
            }
            
        except Exception as e:
            # Clean up file if something went wrong
            if temp_file_path and os.path.exists(temp_file_path):
                os.remove(temp_file_path)
            raise e
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Video upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@api_router.get("/videos")
async def get_videos(limit: int = 50, offset: int = 0):
    """Get videos for current competition round"""
    try:
        round_id = await get_current_competition_round()
        
        videos = await db.videos.find({
            "competition_round": round_id,
            "is_paid": True,
            "filename": {"$ne": ""}
        }).sort("view_count", -1).skip(offset).limit(limit).to_list(limit)
        
        # Serialize videos to remove ObjectId issues
        serialized_videos = [serialize_doc(video) for video in videos]
        
        return {"videos": serialized_videos, "total": len(serialized_videos)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/video/{video_id}")
async def get_video(video_id: str):
    """Get video details"""
    try:
        video = await db.videos.find_one({"id": video_id})
        if not video:
            raise HTTPException(status_code=404, detail="Video not found")
        
        return serialize_doc(video)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/video/{video_id}/stream")
async def stream_video(video_id: str):
    """Stream video file"""
    try:
        video = await db.videos.find_one({"id": video_id})
        if not video or not video.get("file_path"):
            raise HTTPException(status_code=404, detail="Video not found")
        
        file_path = Path(video["file_path"])
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Video file not found")
        
        return FileResponse(
            file_path,
            media_type="video/mp4",
            filename=video["filename"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/feed/personalized")
async def get_personalized_feed(
    user_id: Optional[str] = None,
    limit: int = 10,
    algorithm_version: str = "1.0"
):
    """Get personalized video feed using recommendation algorithm"""
    try:
        engine = await get_algorithm_engine()
        feed = await engine.get_personalized_feed(user_id, limit)
        
        return {
            "feed": feed,
            "algorithm_version": algorithm_version,
            "total_items": len(feed)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get personalized feed: {str(e)}")

@api_router.post("/interaction")
async def record_interaction(
    video_id: str,
    interaction_type: str,  # "view", "like", "comment", "share", "watch_time"
    user_id: Optional[str] = None,
    value: Optional[float] = None  # For watch_time
):
    """Record user interaction and update algorithm"""
    try:
        engine = await get_algorithm_engine()
        
        # Record interaction
        interaction = VideoInteraction(
            video_id=video_id,
            user_id=user_id,
            interaction_type=interaction_type,
            value=value
        )
        await db.video_interactions.insert_one(interaction.dict())
        
        # Update video metrics
        await engine.update_video_metrics(video_id, interaction_type, value)
        
        # Learn user preferences if user is logged in
        if user_id:
            await engine.learn_user_preferences(user_id, video_id, interaction_type, value)
        
        return {"message": "Interaction recorded successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to record interaction: {str(e)}")

@api_router.get("/leaderboard")
async def get_leaderboard():
    """Get current competition leaderboard"""
    try:
        round_id = await get_current_competition_round()
        
        # Get top 1000 videos by views
        top_videos = await db.videos.find({
            "competition_round": round_id,
            "is_paid": True,
            "filename": {"$ne": ""}
        }).sort("view_count", -1).limit(1000).to_list(1000)
        
        # Get competition round info
        competition = await db.competition_rounds.find_one({"id": round_id})
        
        # Serialize data
        serialized_videos = [serialize_doc(video) for video in top_videos]
        serialized_competition = serialize_doc(competition)
        
        return {
            "leaderboard": serialized_videos,
            "competition_info": {
                "round_id": round_id,
                "end_date": serialized_competition["end_date"] if serialized_competition else None,
                "total_prize_pool": serialized_competition["prize_pool"] if serialized_competition else 0,
                "total_videos": serialized_competition["total_videos"] if serialized_competition else 0
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    """Handle Stripe webhooks"""
    await init_stripe()
    
    try:
        body = await request.body()
        signature = request.headers.get("stripe-signature")
        
        webhook_response = await stripe_checkout.handle_webhook(body, signature)
        
        if webhook_response.event_type == "payment_intent.succeeded":
            # Update payment session status
            await db.payment_sessions.update_one(
                {"session_id": webhook_response.session_id},
                {
                    "$set": {
                        "status": "paid",
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            # Mark video as paid
            video_id = webhook_response.metadata.get("video_id")
            if video_id:
                await db.videos.update_one(
                    {"id": video_id},
                    {"$set": {"is_paid": True}}
                )
        
        return {"status": "success"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Webhook failed: {str(e)}")

# Include router
# Include main API router
app.include_router(api_router)

# Fix dependency injection for admin routes
from functools import wraps

def inject_db(route_func):
    @wraps(route_func)
    async def wrapper(*args, **kwargs):
        # Inject db into kwargs
        kwargs['db'] = db
        return await route_func(*args, **kwargs)
    return wrapper

# Apply db injection to admin routes
for route in admin_router.routes:
    if hasattr(route, 'endpoint'):
        route.endpoint = inject_db(route.endpoint)

# Include admin router
app.include_router(admin_router)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()