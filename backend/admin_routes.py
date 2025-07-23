# Admin Dashboard API Routes
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import jwt
import bcrypt
import os
from pydantic import BaseModel

from models import (
    AdminUser, AdminLog, Competition, Video, User, AlgorithmConfig,
    CompetitionStatus, VideoStatus, CreditTransaction
)
from algorithm import VideoRecommendationEngine

admin_router = APIRouter(prefix="/api/admin", tags=["admin"])
security = HTTPBearer()

SECRET_KEY = os.environ.get('ADMIN_SECRET_KEY', 'pego_admin_secret_key_change_in_production')
ALGORITHM = "HS256"

class AdminLogin(BaseModel):
    username: str
    password: str

class AdminCreate(BaseModel):
    username: str
    email: str
    password: str
    role: str = "admin"  # admin, moderator, super_admin

class CompetitionCreate(BaseModel):
    title: str
    description: Optional[str] = ""
    duration_days: int = 7
    entry_fee: float = 30.0
    winner_count: int = 1000
    special_winner_count: int = 10

class VideoModerationAction(BaseModel):
    video_ids: List[str]
    action: str  # "suspend", "approve", "feature", "remove_feature", "delete"
    reason: Optional[str] = ""

class UserModerationAction(BaseModel):
    user_ids: List[str]
    action: str  # "suspend", "activate", "verify", "unverify", "ban", "unban"
    reason: Optional[str] = ""

class SystemSettings(BaseModel):
    video_price: float = 30.0  # THB per video
    prize_percentage: float = 70.0  # Percentage of revenue for prizes
    competition_duration_days: int = 7
    max_video_size_mb: int = 100
    credits_per_thb: int = 1  # 1 THB = 1 Credit

class FinancialSettings(BaseModel):
    video_upload_price: float
    prize_pool_percentage: float
    admin_fee_percentage: float = 30.0
    min_payout_amount: float = 100.0

# Database dependency
def get_db():
    from server import db
    return db

# Dependency functions
async def get_current_admin(credentials: HTTPAuthorizationCredentials = Depends(security), db=Depends(get_db)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        admin_id: str = payload.get("sub")
        if admin_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    admin = await db.admin_users.find_one({"id": admin_id, "is_active": True})
    if admin is None:
        raise HTTPException(status_code=401, detail="Admin not found")
    
    return AdminUser(**admin)

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

async def log_admin_action(db, admin_id: str, action: str, target_type: str, target_id: str, details: Dict[str, Any] = {}):
    log = AdminLog(
        admin_id=admin_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        details=details
    )
    await db.admin_logs.insert_one(log.dict())

def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

# Authentication routes
@admin_router.post("/register")
async def create_admin(admin_data: AdminCreate, db=Depends(get_db)):
    """Create new admin user (for setup only)"""
    # Check if admin with username already exists
    existing_admin = await db.admin_users.find_one({"username": admin_data.username})
    if existing_admin:
        raise HTTPException(status_code=400, detail="Admin username already exists")
    
    # Check if admin with email already exists
    existing_email = await db.admin_users.find_one({"email": admin_data.email})
    if existing_email:
        raise HTTPException(status_code=400, detail="Admin email already exists")
    
    # Create admin user
    admin_user = AdminUser(
        username=admin_data.username,
        email=admin_data.email,
        password_hash=hash_password(admin_data.password),
        role=admin_data.role,
        permissions=["full_access"]  # Default permissions
    )
    
    await db.admin_users.insert_one(admin_user.dict())
    
    return {
        "message": "Admin created successfully",
        "admin": {
            "id": admin_user.id,
            "username": admin_user.username,
            "email": admin_user.email,
            "role": admin_user.role
        }
    }

@admin_router.post("/login")
async def admin_login(login_data: AdminLogin, db=Depends(get_db)):
    admin = await db.admin_users.find_one({"username": login_data.username, "is_active": True})
    if not admin:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Verify password
    if not verify_password(login_data.password, admin["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Update last login
    await db.admin_users.update_one(
        {"id": admin["id"]},
        {"$set": {"last_login": datetime.utcnow()}}
    )
    
    # Create JWT token
    access_token = jwt.encode(
        {"sub": admin["id"], "exp": datetime.utcnow() + timedelta(hours=24)},
        SECRET_KEY,
        algorithm=ALGORITHM
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "admin": {
            "id": admin["id"],
            "username": admin["username"],
            "email": admin["email"],
            "role": admin["role"]
        }
    }

# Dashboard overview
@admin_router.get("/dashboard")
async def get_dashboard_stats(admin: AdminUser = Depends(get_current_admin), db=Depends(get_db)):
    # Get current date ranges
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = now - timedelta(days=7)
    month_start = now - timedelta(days=30)
    
    # Get current active competition
    current_competition = await db.competitions.find_one({"status": "active"})
    
    # Basic stats
    stats = {
        "overview": {
            "total_users": await db.users.count_documents({}),
            "active_users": await db.users.count_documents({"last_active": {"$gte": week_start}}),
            "total_videos": await db.videos.count_documents({}),
            "active_videos": await db.videos.count_documents({"status": "active"}),
            "total_competitions": await db.competitions.count_documents({}),
            "active_competitions": await db.competitions.count_documents({"status": "active"})
        },
        "today": {
            "new_users": await db.users.count_documents({"created_at": {"$gte": today_start}}),
            "new_videos": await db.videos.count_documents({"upload_date": {"$gte": today_start}}),
            "total_views": 0,  # Will calculate below
            "total_revenue": 0
        },
        "current_competition": None
    }
    
    # Calculate today's views and revenue
    today_videos = await db.videos.find({"upload_date": {"$gte": today_start}}).to_list(None)
    stats["today"]["total_views"] = sum(video.get("view_count", 0) for video in today_videos)
    stats["today"]["total_revenue"] = len(today_videos) * 30  # 30 THB per video
    
    # Current competition details
    if current_competition:
        competition_videos = await db.videos.find({
            "competition_round": current_competition["id"],
            "is_paid": True
        }).to_list(None)
        
        stats["current_competition"] = {
            "id": current_competition["id"],
            "title": current_competition["title"],
            "start_date": current_competition["start_date"],
            "end_date": current_competition["end_date"],
            "participant_count": len(set(video["user_id"] for video in competition_videos)),
            "video_count": len(competition_videos),
            "total_revenue": current_competition.get("total_revenue", 0),
            "prize_pool": current_competition.get("prize_pool", 0),
            "days_remaining": (current_competition["end_date"] - now).days
        }
    
    return stats

# Competition management
@admin_router.get("/competitions")
async def get_competitions(
    status: Optional[str] = None,
    limit: int = Query(50, le=100),
    offset: int = 0,
    admin: AdminUser = Depends(get_current_admin),
    db=Depends(get_db)
):
    query = {}
    if status:
        query["status"] = status
    
    competitions = await db.competitions.find(query).sort("created_at", -1).skip(offset).limit(limit).to_list(limit)
    total = await db.competitions.count_documents(query)
    
    return {
        "competitions": competitions,
        "total": total,
        "limit": limit,
        "offset": offset
    }

@admin_router.post("/competitions")
async def create_competition(
    competition_data: CompetitionCreate,
    admin: AdminUser = Depends(get_current_admin),
    db=Depends(get_db)
):
    # End current active competition if exists
    await db.competitions.update_many(
        {"status": "active"},
        {"$set": {"status": "ended", "end_date": datetime.utcnow()}}
    )
    
    # Create new competition
    start_date = datetime.utcnow()
    end_date = start_date + timedelta(days=competition_data.duration_days)
    
    competition = Competition(
        title=competition_data.title,
        description=competition_data.description,
        start_date=start_date,
        end_date=end_date,
        entry_fee=competition_data.entry_fee,
        winner_count=competition_data.winner_count,
        special_winner_count=competition_data.special_winner_count,
        status=CompetitionStatus.ACTIVE,
        created_by=admin.id
    )
    
    result = await db.competitions.insert_one(competition.dict())
    competition_id = str(result.inserted_id)
    
    # Log admin action
    await log_admin_action(
        db, admin.id, "create_competition", "competition", competition_id,
        {"title": competition.title, "duration_days": competition_data.duration_days}
    )
    
    return {"message": "Competition created successfully", "competition_id": competition_id}

@admin_router.put("/competitions/{competition_id}/end")
async def end_competition(
    competition_id: str,
    admin: AdminUser = Depends(get_current_admin),
    db=Depends(get_db)
):
    competition = await db.competitions.find_one({"id": competition_id})
    if not competition:
        raise HTTPException(status_code=404, detail="Competition not found")
    
    # Calculate final results
    algorithm = VideoRecommendationEngine(db)
    
    # Get all videos from this competition
    videos = await db.videos.find({
        "competition_round": competition_id,
        "is_paid": True,
        "status": "active"
    }).to_list(None)
    
    # Calculate final scores and rankings
    scored_videos = []
    for video_data in videos:
        video = Video(**video_data)
        score = await algorithm.calculate_composite_score(video, competition_id)
        scored_videos.append({
            "video_id": video.id,
            "user_id": video.user_id,
            "score": score.total_score,
            "view_count": video.view_count
        })
    
    # Sort by score
    scored_videos.sort(key=lambda x: x["score"], reverse=True)
    
    # Determine winners
    winners = []
    for i, video in enumerate(scored_videos[:competition["winner_count"]], 1):
        is_special = i <= competition["special_winner_count"]
        winners.append({
            "rank": i,
            "video_id": video["video_id"],
            "user_id": video["user_id"],
            "score": video["score"],
            "is_special_winner": is_special
        })
    
    # Update competition
    await db.competitions.update_one(
        {"id": competition_id},
        {
            "$set": {
                "status": "ended",
                "end_date": datetime.utcnow(),
                "winners": winners
            }
        }
    )
    
    # Log admin action
    await log_admin_action(
        db, admin.id, "end_competition", "competition", competition_id,
        {"winner_count": len(winners), "total_participants": len(videos)}
    )
    
    return {
        "message": "Competition ended successfully",
        "winners": winners[:20],  # Return top 20 winners
        "total_winners": len(winners)
    }

# Video management
@admin_router.get("/videos")
async def get_videos(
    status: Optional[str] = None,
    competition_id: Optional[str] = None,
    user_id: Optional[str] = None,
    limit: int = Query(50, le=100),
    offset: int = 0,
    admin: AdminUser = Depends(get_current_admin),
    db=Depends(get_db)
):
    query = {}
    if status:
        query["status"] = status
    if competition_id:
        query["competition_round"] = competition_id
    if user_id:
        query["user_id"] = user_id
    
    videos = await db.videos.find(query).sort("upload_date", -1).skip(offset).limit(limit).to_list(limit)
    total = await db.videos.count_documents(query)
    
    # Enrich with user data and serialize
    serialized_videos = []
    for video in videos:
        user = await db.users.find_one({"id": video["user_id"]})
        if user:
            video["user"] = {
                "username": user["username"],
                "display_name": user["display_name"],
                "is_verified": user.get("is_verified", False)
            }
        serialized_videos.append(serialize_doc(video))
    
    return {
        "videos": serialized_videos,
        "total": total,
        "limit": limit,
        "offset": offset
    }

@admin_router.post("/videos/moderate")
async def moderate_videos(
    moderation: VideoModerationAction,
    admin: AdminUser = Depends(get_current_admin),
    db=Depends(get_db)
):
    if moderation.action not in ["suspend", "approve", "feature", "remove_feature"]:
        raise HTTPException(status_code=400, detail="Invalid moderation action")
    
    update_data = {}
    if moderation.action == "suspend":
        update_data["status"] = VideoStatus.SUSPENDED
    elif moderation.action == "approve":
        update_data["status"] = VideoStatus.ACTIVE
    elif moderation.action == "feature":
        update_data["is_featured"] = True
    elif moderation.action == "remove_feature":
        update_data["is_featured"] = False
    
    # Update videos
    result = await db.videos.update_many(
        {"id": {"$in": moderation.video_ids}},
        {"$set": update_data}
    )
    
    # Log admin action
    for video_id in moderation.video_ids:
        await log_admin_action(
            db, admin.id, f"moderate_video_{moderation.action}", "video", video_id,
            {"reason": moderation.reason}
        )
    
    return {
        "message": f"Moderated {result.modified_count} videos",
        "action": moderation.action,
        "affected_count": result.modified_count
    }

# User management
@admin_router.get("/users")
async def get_users(
    is_verified: Optional[bool] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    limit: int = Query(50, le=100),
    offset: int = 0,
    admin: AdminUser = Depends(get_current_admin),
    db=Depends(get_db)
):
    query = {}
    if is_verified is not None:
        query["is_verified"] = is_verified
    if is_active is not None:
        query["is_active"] = is_active
    if search:
        query["$or"] = [
            {"username": {"$regex": search, "$options": "i"}},
            {"display_name": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}}
        ]
    
    users = await db.users.find(query).sort("created_at", -1).skip(offset).limit(limit).to_list(limit)
    total = await db.users.count_documents(query)
    
    # Add video count for each user and serialize
    serialized_users = []
    for user in users:
        video_count = await db.videos.count_documents({"user_id": user["id"]})
        user["video_count"] = video_count
        serialized_users.append(serialize_doc(user))
    
    return {
        "users": serialized_users,
        "total": total,
        "limit": limit,
        "offset": offset
    }

@admin_router.post("/users/moderate")
async def moderate_users(
    moderation: UserModerationAction,
    admin: AdminUser = Depends(get_current_admin),
    db=Depends(get_db)
):
    if moderation.action not in ["suspend", "activate", "verify", "unverify"]:
        raise HTTPException(status_code=400, detail="Invalid moderation action")
    
    update_data = {}
    if moderation.action == "suspend":
        update_data["is_active"] = False
    elif moderation.action == "activate":
        update_data["is_active"] = True
    elif moderation.action == "verify":
        update_data["is_verified"] = True
    elif moderation.action == "unverify":
        update_data["is_verified"] = False
    
    # Update users
    result = await db.users.update_many(
        {"id": {"$in": moderation.user_ids}},
        {"$set": update_data}
    )
    
    # Log admin actions
    for user_id in moderation.user_ids:
        await log_admin_action(
            db, admin.id, f"moderate_user_{moderation.action}", "user", user_id,
            {"reason": moderation.reason}
        )
    
    return {
        "message": f"Moderated {result.modified_count} users",
        "action": moderation.action,
        "affected_count": result.modified_count
    }

# Algorithm management
@admin_router.get("/algorithm/config")
async def get_algorithm_config(admin: AdminUser = Depends(get_current_admin), db=Depends(get_db)):
    config = await db.algorithm_configs.find_one({"is_active": True})
    if not config:
        raise HTTPException(status_code=404, detail="No active algorithm configuration found")
    
    return config

@admin_router.put("/algorithm/config")
async def update_algorithm_config(
    config_data: dict,
    admin: AdminUser = Depends(get_current_admin),
    db=Depends(get_db)
):
    # Validate config data
    try:
        updated_config = AlgorithmConfig(**config_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid configuration: {str(e)}")
    
    # Deactivate current config
    await db.algorithm_configs.update_many(
        {"is_active": True},
        {"$set": {"is_active": False}}
    )
    
    # Create new active config
    updated_config.created_at = datetime.utcnow()
    result = await db.algorithm_configs.insert_one(updated_config.dict())
    
    # Log admin action
    await log_admin_action(
        db, admin.id, "update_algorithm_config", "algorithm", str(result.inserted_id),
        config_data
    )
    
    return {"message": "Algorithm configuration updated successfully"}

# Analytics
@admin_router.get("/analytics/engagement")
async def get_engagement_analytics(
    days: int = Query(7, le=30),
    admin: AdminUser = Depends(get_current_admin),
    db=Depends(get_db)
):
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Aggregate engagement data
    pipeline = [
        {"$match": {"created_at": {"$gte": start_date}}},
        {"$group": {
            "_id": {
                "date": {"$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}},
                "interaction_type": "$interaction_type"
            },
            "count": {"$sum": 1}
        }},
        {"$sort": {"_id.date": 1}}
    ]
    
    interactions = await db.video_interactions.aggregate(pipeline).to_list(None)
    
    # Format data for charts
    daily_data = {}
    for item in interactions:
        date = item["_id"]["date"]
        interaction_type = item["_id"]["interaction_type"]
        
        if date not in daily_data:
            daily_data[date] = {}
        
        daily_data[date][interaction_type] = item["count"]
    
    return {
        "period": f"Last {days} days",
        "daily_engagement": daily_data
    }

# Admin logs
@admin_router.get("/logs")
async def get_admin_logs(
    action: Optional[str] = None,
    target_type: Optional[str] = None,
    limit: int = Query(100, le=500),
    offset: int = 0,
    admin: AdminUser = Depends(get_current_admin),
    db=Depends(get_db)
):
    query = {}
    if action:
        query["action"] = action
    if target_type:
        query["target_type"] = target_type
    
    logs = await db.admin_logs.find(query).sort("created_at", -1).skip(offset).limit(limit).to_list(limit)
    total = await db.admin_logs.count_documents(query)
    
    # Enrich with admin info
    for log in logs:
        admin_user = await db.admin_users.find_one({"id": log["admin_id"]})
        if admin_user:
            log["admin_username"] = admin_user["username"]
    
    return {
        "logs": logs,
        "total": total,
        "limit": limit,
        "offset": offset
    }

# Enhanced User Management
@admin_router.get("/users/{user_id}")
async def get_user_detail(
    user_id: str,
    admin: AdminUser = Depends(get_current_admin),
    db=Depends(get_db)
):
    """Get detailed user information"""
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get user's videos
    videos = await db.videos.find({"user_id": user_id}).to_list(None)
    
    # Get user's credit transactions
    transactions = await db.credit_transactions.find({"user_id": user_id}).sort("created_at", -1).limit(50).to_list(50)
    
    # Calculate stats
    total_spent = sum(abs(t["amount"]) for t in transactions if t["amount"] < 0)
    total_topped_up = sum(t["amount"] for t in transactions if t["amount"] > 0)
    total_views = sum(v.get("view_count", 0) for v in videos)
    total_likes = sum(v.get("like_count", 0) for v in videos)
    
    return {
        "user": serialize_doc(user),
        "stats": {
            "video_count": len(videos),
            "total_views": total_views,
            "total_likes": total_likes,
            "total_spent_credits": total_spent,
            "total_topped_up_credits": total_topped_up,
            "current_credits": user.get("credits", 0)
        },
        "recent_videos": serialize_doc(videos[:10]),  # Last 10 videos
        "recent_transactions": serialize_doc(transactions[:20])  # Last 20 transactions
    }

@admin_router.post("/users/{user_id}/ban")
async def ban_user(
    user_id: str,
    reason: str = "",
    admin: AdminUser = Depends(get_current_admin),
    db=Depends(get_db)
):
    """Ban a user"""
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Ban user
    await db.users.update_one(
        {"id": user_id},
        {"$set": {"is_active": False, "banned_at": datetime.utcnow(), "ban_reason": reason}}
    )
    
    # Suspend all user's videos
    await db.videos.update_many(
        {"user_id": user_id},
        {"$set": {"status": VideoStatus.SUSPENDED}}
    )
    
    # Log action
    await log_admin_action(
        db, admin.id, "ban_user", "user", user_id,
        {"reason": reason, "username": user["username"]}
    )
    
    return {"message": f"User {user['username']} has been banned"}

@admin_router.post("/users/{user_id}/unban")
async def unban_user(
    user_id: str,
    admin: AdminUser = Depends(get_current_admin),
    db=Depends(get_db)
):
    """Unban a user"""
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Unban user
    await db.users.update_one(
        {"id": user_id},
        {
            "$set": {"is_active": True},
            "$unset": {"banned_at": "", "ban_reason": ""}
        }
    )
    
    # Reactivate user's videos (except those manually suspended)
    await db.videos.update_many(
        {"user_id": user_id, "status": VideoStatus.SUSPENDED},
        {"$set": {"status": VideoStatus.ACTIVE}}
    )
    
    # Log action
    await log_admin_action(
        db, admin.id, "unban_user", "user", user_id,
        {"username": user["username"]}
    )
    
    return {"message": f"User {user['username']} has been unbanned"}

@admin_router.post("/users/{user_id}/credits/adjust")
async def adjust_user_credits(
    user_id: str,
    request: Request,
    admin: AdminUser = Depends(get_current_admin),
    db=Depends(get_db)
):
    """Adjust user's credit balance"""
    body = await request.json()
    amount = body.get("amount", 0)  # Can be positive or negative
    reason = body.get("reason", "Admin adjustment")
    
    if amount == 0:
        raise HTTPException(status_code=400, detail="Amount cannot be zero")
    
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if user would have negative credits after adjustment
    current_credits = user.get("credits", 0)
    if current_credits + amount < 0:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot adjust credits. User has {current_credits} credits, adjustment would result in negative balance"
        )
    
    # Update user credits
    await db.users.update_one(
        {"id": user_id},
        {"$inc": {"credits": amount}}
    )
    
    # Record transaction
    transaction = CreditTransaction(
        user_id=user_id,
        amount=amount,
        transaction_type="admin_adjustment",
        description=f"Admin adjustment: {reason}",
        status="completed"
    )
    await db.credit_transactions.insert_one(transaction.dict())
    
    # Log action
    await log_admin_action(
        db, admin.id, "adjust_user_credits", "user", user_id,
        {"amount": amount, "reason": reason, "username": user["username"]}
    )
    
    new_balance = current_credits + amount
    return {
        "message": f"Credits adjusted successfully",
        "previous_balance": current_credits,
        "adjustment": amount,
        "new_balance": new_balance
    }

# Enhanced Video Management
@admin_router.delete("/videos/{video_id}")
async def delete_video(
    video_id: str,
    reason: str = "",
    admin: AdminUser = Depends(get_current_admin),
    db=Depends(get_db)
):
    """Permanently delete a video"""
    video = await db.videos.find_one({"id": video_id})
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    # Delete video file from filesystem
    import os
    from pathlib import Path
    if video.get("file_path") and os.path.exists(video["file_path"]):
        try:
            os.remove(video["file_path"])
        except Exception as e:
            print(f"Error deleting video file: {e}")
    
    # Delete from database
    await db.videos.delete_one({"id": video_id})
    
    # Delete related interactions
    await db.video_interactions.delete_many({"video_id": video_id})
    
    # Log action
    await log_admin_action(
        db, admin.id, "delete_video", "video", video_id,
        {"reason": reason, "title": video.get("title", ""), "user_id": video.get("user_id", "")}
    )
    
    return {"message": "Video deleted successfully"}

@admin_router.get("/videos/{video_id}/analytics")
async def get_video_analytics(
    video_id: str,
    admin: AdminUser = Depends(get_current_admin),
    db=Depends(get_db)
):
    """Get detailed analytics for a video"""
    video = await db.videos.find_one({"id": video_id})
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    # Get interactions
    interactions = await db.video_interactions.find({"video_id": video_id}).to_list(None)
    
    # Analyze interactions
    interaction_stats = {}
    hourly_views = {}
    
    for interaction in interactions:
        interaction_type = interaction["interaction_type"]
        created_at = interaction["created_at"]
        hour = created_at.strftime("%Y-%m-%d %H:00")
        
        # Count by type
        interaction_stats[interaction_type] = interaction_stats.get(interaction_type, 0) + 1
        
        # Hourly views
        if interaction_type == "view":
            hourly_views[hour] = hourly_views.get(hour, 0) + 1
    
    # Get user info
    user = await db.users.find_one({"id": video["user_id"]})
    
    return {
        "video": video,
        "user": user,
        "total_interactions": len(interactions),
        "interaction_breakdown": interaction_stats,
        "hourly_views": hourly_views,
        "engagement_rate": round((interaction_stats.get("like", 0) + interaction_stats.get("comment", 0)) / max(interaction_stats.get("view", 1), 1) * 100, 2)
    }

# Financial Management
@admin_router.get("/financial/overview")
async def get_financial_overview(
    days: int = Query(30, le=365),
    admin: AdminUser = Depends(get_current_admin),
    db=Depends(get_db)
):
    """Get financial overview and statistics"""
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Get all credit transactions
    transactions = await db.credit_transactions.find({
        "created_at": {"$gte": start_date}
    }).to_list(None)
    
    # Get all competition rounds
    competitions = await db.competition_rounds.find({
        "start_date": {"$gte": start_date}
    }).to_list(None)
    
    # Calculate totals
    total_revenue = sum(comp.get("total_revenue", 0) for comp in competitions)
    total_prizes = sum(comp.get("prize_pool", 0) for comp in competitions)
    admin_revenue = total_revenue - total_prizes
    
    # Credit analysis
    credit_topups = [t for t in transactions if t["amount"] > 0]
    credit_spending = [t for t in transactions if t["amount"] < 0]
    
    total_credits_sold = sum(t["amount"] for t in credit_topups)
    total_credits_spent = sum(abs(t["amount"]) for t in credit_spending)
    
    # Daily breakdown
    daily_revenue = {}
    for comp in competitions:
        date = comp["start_date"].strftime("%Y-%m-%d")
        daily_revenue[date] = daily_revenue.get(date, 0) + comp.get("total_revenue", 0)
    
    return {
        "period": f"Last {days} days",
        "overview": {
            "total_revenue": total_revenue,
            "total_prizes_paid": total_prizes,
            "admin_revenue": admin_revenue,
            "profit_margin": round((admin_revenue / max(total_revenue, 1)) * 100, 2)
        },
        "credits": {
            "total_sold": total_credits_sold,
            "total_spent": total_credits_spent,
            "credits_in_circulation": total_credits_sold - total_credits_spent
        },
        "daily_revenue": daily_revenue,
        "active_competitions": await db.competition_rounds.count_documents({"is_active": True}),
        "total_users": await db.users.count_documents({}),
        "active_users": await db.users.count_documents({"last_active": {"$gte": start_date}})
    }

@admin_router.get("/financial/settings")
async def get_financial_settings(admin: AdminUser = Depends(get_current_admin), db=Depends(get_db)):
    """Get current financial settings"""
    settings = await db.system_settings.find_one({"type": "financial"})
    if not settings:
        # Return default settings
        return {
            "video_upload_price": 30.0,
            "prize_pool_percentage": 70.0,
            "admin_fee_percentage": 30.0,
            "credits_per_thb": 1,
            "min_payout_amount": 100.0
        }
    return settings.get("settings", {})

@admin_router.put("/financial/settings")
async def update_financial_settings(
    settings: FinancialSettings,
    admin: AdminUser = Depends(get_current_admin),
    db=Depends(get_db)
):
    """Update financial settings"""
    # Validate settings
    if settings.prize_pool_percentage + settings.admin_fee_percentage != 100.0:
        raise HTTPException(
            status_code=400,
            detail="Prize pool percentage and admin fee percentage must sum to 100%"
        )
    
    # Update settings
    await db.system_settings.update_one(
        {"type": "financial"},
        {
            "$set": {
                "type": "financial",
                "settings": settings.dict(),
                "updated_at": datetime.utcnow(),
                "updated_by": admin.id
            }
        },
        upsert=True
    )
    
    # Log action
    await log_admin_action(
        db, admin.id, "update_financial_settings", "system", "financial_settings",
        settings.dict()
    )
    
    return {"message": "Financial settings updated successfully"}

# System Settings
@admin_router.get("/system/settings")
async def get_system_settings(admin: AdminUser = Depends(get_current_admin), db=Depends(get_db)):
    """Get system settings"""
    settings = await db.system_settings.find_one({"type": "system"})
    if not settings:
        return {
            "video_price": 30.0,
            "prize_percentage": 70.0,
            "competition_duration_days": 7,
            "max_video_size_mb": 100,
            "credits_per_thb": 1
        }
    return settings.get("settings", {})

@admin_router.put("/system/settings")
async def update_system_settings(
    settings: SystemSettings,
    admin: AdminUser = Depends(get_current_admin),
    db=Depends(get_db)
):
    """Update system settings"""
    await db.system_settings.update_one(
        {"type": "system"},
        {
            "$set": {
                "type": "system",
                "settings": settings.dict(),
                "updated_at": datetime.utcnow(),
                "updated_by": admin.id
            }
        },
        upsert=True
    )
    
    # Log action
    await log_admin_action(
        db, admin.id, "update_system_settings", "system", "system_settings",
        settings.dict()
    )
    
    return {"message": "System settings updated successfully"}

# Statistics and Analytics
@admin_router.get("/analytics/users")
async def get_user_analytics(
    days: int = Query(30, le=365),
    admin: AdminUser = Depends(get_current_admin),
    db=Depends(get_db)
):
    """Get user analytics"""
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # User growth
    total_users = await db.users.count_documents({})
    new_users = await db.users.count_documents({"created_at": {"$gte": start_date}})
    active_users = await db.users.count_documents({"last_active": {"$gte": start_date}})
    
    # Top users by activity
    pipeline = [
        {"$match": {"created_at": {"$gte": start_date}}},
        {"$lookup": {
            "from": "videos",
            "localField": "id",
            "foreignField": "user_id",
            "as": "videos"
        }},
        {"$addFields": {
            "video_count": {"$size": "$videos"},
            "total_views": {"$sum": "$videos.view_count"}
        }},
        {"$sort": {"total_views": -1}},
        {"$limit": 10}
    ]
    
    top_users = await db.users.aggregate(pipeline).to_list(10)
    
    return {
        "period": f"Last {days} days",
        "summary": {
            "total_users": total_users,
            "new_users": new_users,
            "active_users": active_users,
            "retention_rate": round((active_users / max(total_users, 1)) * 100, 2)
        },
        "top_creators": top_users
    }