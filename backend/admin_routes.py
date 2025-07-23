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

# Dependency functions
async def get_current_admin(credentials: HTTPAuthorizationCredentials = Depends(security), db=None):
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
async def create_admin(admin_data: AdminCreate, db):
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
async def admin_login(login_data: AdminLogin, db):
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
async def get_dashboard_stats(admin: AdminUser = Depends(get_current_admin), db=None):
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
    db=None
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
    db=None
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
    db=None
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
    db=None
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
    
    # Enrich with user data
    for video in videos:
        user = await db.users.find_one({"id": video["user_id"]})
        if user:
            video["user"] = {
                "username": user["username"],
                "display_name": user["display_name"],
                "is_verified": user.get("is_verified", False)
            }
    
    return {
        "videos": videos,
        "total": total,
        "limit": limit,
        "offset": offset
    }

@admin_router.post("/videos/moderate")
async def moderate_videos(
    moderation: VideoModerationAction,
    admin: AdminUser = Depends(get_current_admin),
    db=None
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
    db=None
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
    
    # Add video count for each user
    for user in users:
        video_count = await db.videos.count_documents({"user_id": user["id"]})
        user["video_count"] = video_count
    
    return {
        "users": users,
        "total": total,
        "limit": limit,
        "offset": offset
    }

@admin_router.post("/users/moderate")
async def moderate_users(
    moderation: UserModerationAction,
    admin: AdminUser = Depends(get_current_admin),
    db=None
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
async def get_algorithm_config(admin: AdminUser = Depends(get_current_admin), db=None):
    config = await db.algorithm_configs.find_one({"is_active": True})
    if not config:
        raise HTTPException(status_code=404, detail="No active algorithm configuration found")
    
    return config

@admin_router.put("/algorithm/config")
async def update_algorithm_config(
    config_data: dict,
    admin: AdminUser = Depends(get_current_admin),
    db=None
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
    db=None
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
    db=None
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