# Video Recommendation Algorithm Models
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uuid
from enum import Enum

class VideoStatus(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    SUSPENDED = "suspended"

class CompetitionStatus(str, Enum):
    ACTIVE = "active"
    ENDED = "ended"
    DRAFT = "draft"

class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    display_name: str
    email: Optional[str] = None  # Optional for phone-only users
    phone: Optional[str] = None  # Optional for email-only users
    google_id: Optional[str] = None  # For Google OAuth
    avatar_url: Optional[str] = None
    bio: Optional[str] = ""
    is_verified: bool = False
    follower_count: int = 0
    following_count: int = 0
    total_likes: int = 0
    total_views: int = 0
    credits: int = 0  # User credits for uploads (30 credits = 1 video)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_active: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True

class Video(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: Optional[str] = ""
    hashtags: List[str] = []
    user_id: str
    filename: str
    file_path: str
    thumbnail_url: Optional[str] = None
    duration: Optional[float] = None
    file_size: int
    
    # Engagement metrics
    view_count: int = 0
    like_count: int = 0
    comment_count: int = 0
    share_count: int = 0
    
    # Algorithm factors
    engagement_rate: float = 0.0
    completion_rate: float = 0.0  # How often people watch to the end
    replay_rate: float = 0.0      # How often people replay
    time_watched: float = 0.0     # Total minutes watched
    
    # Competition data
    competition_round: str
    is_paid: bool = False
    payment_session_id: Optional[str] = None
    
    # Content moderation
    status: VideoStatus = VideoStatus.ACTIVE
    is_featured: bool = False
    
    # Timestamps
    upload_date: datetime = Field(default_factory=datetime.utcnow)
    published_at: Optional[datetime] = None
    last_updated: datetime = Field(default_factory=datetime.utcnow)

class VideoInteraction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    video_id: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None  # For anonymous users
    interaction_type: str  # "view", "like", "comment", "share", "watch_time"
    value: Optional[float] = None  # For watch_time, replay_count etc
    metadata: Optional[Dict[str, Any]] = {}
    created_at: datetime = Field(default_factory=datetime.utcnow)

class UserFollow(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    follower_id: str
    following_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Comment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    video_id: str
    user_id: str
    parent_id: Optional[str] = None  # For replies
    content: str
    like_count: int = 0
    reply_count: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True

class Competition(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: Optional[str] = ""
    start_date: datetime
    end_date: datetime
    entry_fee: float = 30.0  # THB
    total_revenue: float = 0.0
    prize_pool: float = 0.0  # 70% of revenue
    participant_count: int = 0
    video_count: int = 0
    status: CompetitionStatus = CompetitionStatus.DRAFT
    
    # Winner configuration
    winner_count: int = 1000  # Top 1000
    special_winner_count: int = 10  # Top 10 get extra prizes
    
    # Algorithm weights for this competition
    view_weight: float = 0.4
    like_weight: float = 0.2
    comment_weight: float = 0.2
    share_weight: float = 0.1
    completion_weight: float = 0.1
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str  # Admin user ID

class AlgorithmScore(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    video_id: str
    competition_id: str
    
    # Individual scores (0-100)
    view_score: float = 0.0
    engagement_score: float = 0.0
    recency_score: float = 0.0
    quality_score: float = 0.0
    user_score: float = 0.0  # Based on user's past performance
    
    # Final composite score
    total_score: float = 0.0
    rank_position: int = 0
    
    # Metadata
    calculated_at: datetime = Field(default_factory=datetime.utcnow)
    algorithm_version: str = "1.0"

class AdminUser(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    email: str
    password_hash: str
    role: str = "admin"  # admin, moderator, super_admin
    permissions: List[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None
    is_active: bool = True

class AdminLog(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    admin_id: str
    action: str  # "create_competition", "moderate_video", "ban_user" etc
    target_type: str  # "video", "user", "competition"
    target_id: str
    details: Dict[str, Any] = {}
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Algorithm Configuration Models
class AlgorithmConfig(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    version: str
    
    # Time decay factors
    recency_factor: float = 0.3  # How much to favor new content
    half_life_days: int = 7      # Content loses half relevance after N days
    
    # Engagement thresholds
    viral_threshold: float = 0.1  # % of users who need to engage for viral boost
    quality_threshold: float = 0.5  # Minimum completion rate for quality
    
    # User preference weights
    follow_boost: float = 2.0     # Boost for followed users
    hashtag_boost: float = 1.5    # Boost for preferred hashtags
    similar_content_boost: float = 1.2
    
    # Content diversity
    max_same_user: int = 2        # Max videos from same user in feed
    max_same_hashtag: int = 3     # Max videos with same hashtag
    
    # Active status
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class UserPreference(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    
    # Content preferences (learned from interactions)
    preferred_hashtags: List[str] = []
    preferred_users: List[str] = []
    preferred_duration: Optional[float] = None  # Preferred video length
    preferred_categories: List[str] = []
    
    # Engagement patterns
    avg_watch_time: float = 0.0
    peak_activity_hours: List[int] = []  # Hours of day when most active
    
    # Negative signals
    skipped_hashtags: List[str] = []
    blocked_users: List[str] = []
    
    updated_at: datetime = Field(default_factory=datetime.utcnow)