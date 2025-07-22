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

# Emergent integrations for payments
from emergentintegrations.payments.stripe.checkout import StripeCheckout, CheckoutSessionResponse, CheckoutStatusResponse, CheckoutSessionRequest

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

# Stripe setup
stripe_api_key = os.environ.get('STRIPE_API_KEY')
stripe_checkout = None

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
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

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

# Routes
@api_router.get("/")
async def root():
    return {"message": "Pego Video Contest Platform API"}

@api_router.post("/upload/initiate")
async def initiate_upload(video_data: VideoCreate):
    """Initiate video upload - creates payment session first"""
    await init_stripe()
    
    if not stripe_checkout:
        raise HTTPException(status_code=500, detail="Payment system not configured")
    
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
        video_id = str(result.inserted_id)
        
        # Create Stripe checkout session for 30 THB
        host_url = "http://localhost:3000"  # Will be updated with actual frontend URL
        success_url = f"{host_url}/upload/success?session_id={{CHECKOUT_SESSION_ID}}&video_id={video_id}"
        cancel_url = f"{host_url}/upload/cancel"
        
        checkout_request = CheckoutSessionRequest(
            amount=30.0,
            currency="thb",
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                "video_id": str(video_id),
                "user_id": video_data.user_id,
                "service": "video_upload"
            }
        )
        
        session: CheckoutSessionResponse = await stripe_checkout.create_checkout_session(checkout_request)
        
        # Store payment session
        payment_session = PaymentSession(
            session_id=session.session_id,
            user_id=video_data.user_id,
            video_id=str(video_id),
            amount=30.0,
            currency="thb",
            status="initiated"
        )
        
        await db.payment_sessions.insert_one(payment_session.dict())
        
        # Update video with payment session
        await db.videos.update_one(
            {"_id": result.inserted_id},
            {"$set": {"payment_session_id": session.session_id}}
        )
        
        return {
            "video_id": str(video_id),
            "checkout_url": session.url,
            "session_id": session.session_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initiate upload: {str(e)}")

@api_router.get("/payment/status/{session_id}")
async def check_payment_status(session_id: str):
    """Check payment status"""
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
                    {"_id": video_id},
                    {"$set": {"is_paid": True}}
                )
        
        return {
            "session_id": session_id,
            "status": status.status,
            "payment_status": status.payment_status,
            "amount": status.amount_total / 100,  # Convert from cents
            "currency": status.currency
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to check payment status: {str(e)}")

@api_router.post("/upload/video/{video_id}")
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

@api_router.post("/video/{video_id}/view")
async def record_view(video_id: str, viewer_data: VideoView):
    """Record video view"""
    try:
        # Check if video exists
        video = await db.videos.find_one({"id": video_id})
        if not video:
            raise HTTPException(status_code=404, detail="Video not found")
        
        # Record view
        view = VideoView(video_id=video_id, viewer_id=viewer_data.viewer_id)
        await db.video_views.insert_one(view.dict())
        
        # Increment view count
        await db.videos.update_one(
            {"id": video_id},
            {"$inc": {"view_count": 1}}
        )
        
        return {"message": "View recorded", "video_id": video_id}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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