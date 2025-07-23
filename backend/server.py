from fastapi import FastAPI, APIRouter, File, UploadFile, HTTPException, Request, Form
from fastapi.responses import StreamingResponse, FileResponse
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

# Import new modules
from models import Video, User, VideoInteraction, Competition, AlgorithmScore, AdminUser
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

# Create upload directories
UPLOAD_DIR = ROOT_DIR / "uploads" / "videos"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Create the main app
app = FastAPI()
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

def generate_promptpay_qr(promptpay_id: str, amount: float) -> dict:
    """Generate PromptPay QR code data and image"""
    try:
        # Generate PromptPay QR code data using pypromptpay
        qr_data = pp_qrcode(account=promptpay_id, money=str(amount), currency="THB")
        
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
async def initiate_upload(video_data: VideoCreate):
    """Initiate video upload - creates video record first, payment later"""
    try:
        # Get current competition round
        round_id = await get_current_competition_round()
        
        # Create video record (unpaid)
        video = VideoUpload(
            filename="",
            file_path="",
            title=video_data.title,
            description=video_data.description,
            user_id=video_data.user_id,
            file_size=0,
            competition_round=round_id,
            is_paid=False
        )
        
        result = await db.videos.insert_one(video.dict())
        video_id = video.id  # Use the custom UUID ID, not MongoDB ObjectId
        
        return {
            "video_id": video_id,
            "message": "Video initiated successfully. Please select payment method."
        }
        
    except Exception as e:
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
            session_id = str(result.inserted_id)
            
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
async def upload_video_file(
    video_id: str,
    file: UploadFile = File(...),
):
    """Upload video file after payment confirmation"""
    try:
        # Check if video exists and is paid
        video_doc = await db.videos.find_one({"id": video_id})
        if not video_doc:
            raise HTTPException(status_code=404, detail="Video not found")
        
        if not video_doc.get("is_paid", False):
            raise HTTPException(status_code=402, detail="Payment required")
        
        # Validate file type and size
        if not file.content_type.startswith("video/"):
            raise HTTPException(status_code=400, detail="File must be a video")
        
        # Check file size (limit to ~100MB for 3-minute videos)
        max_size = 100 * 1024 * 1024  # 100MB
        if file.size > max_size:
            raise HTTPException(status_code=400, detail="File too large (max 100MB)")
        
        # Save file
        file_extension = Path(file.filename).suffix
        filename = f"{video_id}{file_extension}"
        file_path = UPLOAD_DIR / filename
        
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        # Update video record
        await db.videos.update_one(
            {"id": video_id},
            {
                "$set": {
                    "filename": filename,
                    "file_path": str(file_path),
                    "file_size": len(content),
                    "upload_date": datetime.utcnow()
                }
            }
        )
        
        # Update competition round stats
        round_id = video_doc["competition_round"]
        await db.competition_rounds.update_one(
            {"id": round_id},
            {
                "$inc": {
                    "total_revenue": 30.0,
                    "total_videos": 1,
                    "prize_pool": 21.0  # 70% of 30 THB
                }
            }
        )
        
        return {
            "message": "Video uploaded successfully",
            "video_id": video_id,
            "filename": filename
        }
        
    except Exception as e:
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
        
        return {"videos": videos, "total": len(videos)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/video/{video_id}")
async def get_video(video_id: str):
    """Get video details"""
    try:
        video = await db.videos.find_one({"id": video_id})
        if not video:
            raise HTTPException(status_code=404, detail="Video not found")
        
        return video
        
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
        
        return {
            "leaderboard": top_videos,
            "competition_info": {
                "round_id": round_id,
                "end_date": competition["end_date"] if competition else None,
                "total_prize_pool": competition["prize_pool"] if competition else 0,
                "total_videos": competition["total_videos"] if competition else 0
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
app.include_router(api_router)

# Include admin router with dependency injection
@admin_router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def admin_route_with_db(path: str, request: Request):
    # This is a workaround to inject db dependency into admin routes
    # In a real app, you'd use proper dependency injection
    pass

# Add admin router manually
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