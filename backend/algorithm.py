# Advanced Video Recommendation Algorithm
import math
import random
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from collections import defaultdict

from models import Video, User, VideoInteraction, AlgorithmScore, AlgorithmConfig, UserPreference

class VideoRecommendationEngine:
    def __init__(self, db):
        self.db = db
        self.current_config = None
        
    async def get_algorithm_config(self) -> AlgorithmConfig:
        """Get current active algorithm configuration"""
        if not self.current_config:
            config = await self.db.algorithm_configs.find_one({"is_active": True})
            if config:
                self.current_config = AlgorithmConfig(**config)
            else:
                # Create default config
                self.current_config = AlgorithmConfig(
                    name="Default Recommendation Algorithm",
                    version="1.0"
                )
                await self.db.algorithm_configs.insert_one(self.current_config.dict())
        return self.current_config
    
    async def calculate_recency_score(self, video: Video) -> float:
        """Calculate score based on how recent the video is"""
        config = await self.get_algorithm_config()
        
        now = datetime.utcnow()
        age_days = (now - video.upload_date).total_seconds() / 86400  # Convert to days
        
        # Exponential decay based on half-life
        half_life = config.half_life_days
        decay_factor = math.pow(0.5, age_days / half_life)
        
        # Apply recency factor
        recency_score = decay_factor * config.recency_factor * 100
        
        return min(recency_score, 100.0)
    
    async def calculate_engagement_score(self, video: Video) -> float:
        """Calculate engagement score based on likes, comments, shares"""
        if video.view_count == 0:
            return 0.0
        
        # Calculate engagement rate
        total_engagements = video.like_count + video.comment_count + (video.share_count * 2)  # Shares worth 2x
        engagement_rate = total_engagements / video.view_count
        
        # Apply logarithmic scaling to prevent viral videos from dominating
        if engagement_rate > 0:
            engagement_score = min(math.log10(engagement_rate * 100 + 1) * 25, 100.0)
        else:
            engagement_score = 0.0
            
        # Bonus for high completion rate
        if video.completion_rate > 0.7:  # 70% completion rate
            engagement_score *= 1.2
            
        return min(engagement_score, 100.0)
    
    async def calculate_view_score(self, video: Video) -> float:
        """Calculate score based on view count with diminishing returns"""
        if video.view_count == 0:
            return 0.0
        
        # Logarithmic scaling for view count
        view_score = math.log10(video.view_count + 1) * 20
        
        # Cap at 100
        return min(view_score, 100.0)
    
    async def calculate_quality_score(self, video: Video) -> float:
        """Calculate quality score based on completion rate, replay rate"""
        quality_score = 0.0
        
        # Completion rate (0-50 points)
        quality_score += video.completion_rate * 50
        
        # Replay rate (0-30 points)  
        quality_score += video.replay_rate * 30
        
        # Duration bonus - favor videos 15-60 seconds
        if video.duration:
            if 15 <= video.duration <= 60:
                quality_score += 20
            elif 60 < video.duration <= 120:
                quality_score += 10
                
        return min(quality_score, 100.0)
    
    async def calculate_user_score(self, video: Video) -> float:
        """Calculate score based on user's historical performance"""
        # Get user data
        user = await self.db.users.find_one({"id": video.user_id})
        if not user:
            return 50.0  # Default score for new users
        
        user_obj = User(**user)
        
        score = 50.0  # Base score
        
        # Verified user bonus
        if user_obj.is_verified:
            score += 15
            
        # Follower count bonus (logarithmic)
        if user_obj.follower_count > 0:
            follower_boost = min(math.log10(user_obj.follower_count + 1) * 5, 20)
            score += follower_boost
            
        # Average engagement bonus
        if user_obj.total_views > 0:
            avg_engagement = user_obj.total_likes / user_obj.total_views
            if avg_engagement > 0.05:  # 5% average engagement
                score += 15
                
        return min(score, 100.0)
    
    async def calculate_composite_score(self, video: Video, competition_id: str) -> AlgorithmScore:
        """Calculate final composite score for video"""
        
        # Get competition weights
        competition = await self.db.competitions.find_one({"id": competition_id})
        if not competition:
            # Use default weights
            view_weight = 0.4
            like_weight = 0.2
            comment_weight = 0.2
            share_weight = 0.1
            completion_weight = 0.1
        else:
            view_weight = competition.get("view_weight", 0.4)
            like_weight = competition.get("like_weight", 0.2)
            comment_weight = competition.get("comment_weight", 0.2)  
            share_weight = competition.get("share_weight", 0.1)
            completion_weight = competition.get("completion_weight", 0.1)
        
        # Calculate individual scores
        view_score = await self.calculate_view_score(video)
        engagement_score = await self.calculate_engagement_score(video)
        recency_score = await self.calculate_recency_score(video)
        quality_score = await self.calculate_quality_score(video)
        user_score = await self.calculate_user_score(video)
        
        # Calculate weighted total
        total_score = (
            view_score * view_weight +
            engagement_score * (like_weight + comment_weight + share_weight) +
            quality_score * completion_weight +
            recency_score * 0.2 +  # 20% recency weight
            user_score * 0.1       # 10% user reputation weight
        )
        
        return AlgorithmScore(
            video_id=video.id,
            competition_id=competition_id,
            view_score=view_score,
            engagement_score=engagement_score,
            recency_score=recency_score,
            quality_score=quality_score,
            user_score=user_score,
            total_score=min(total_score, 100.0)
        )
    
    async def get_personalized_feed(self, user_id: Optional[str], limit: int = 10) -> List[Dict]:
        """Get personalized video feed for user"""
        config = await self.get_algorithm_config()
        
        # Get current active competition
        current_competition = await self.db.competitions.find_one({"status": "active"})
        if not current_competition:
            return []
        
        # Get user preferences if logged in
        user_preferences = None
        following_ids = []
        if user_id:
            user_pref = await self.db.user_preferences.find_one({"user_id": user_id})
            if user_pref:
                user_preferences = UserPreference(**user_pref)
            
            # Get following list
            follows = await self.db.user_follows.find({"follower_id": user_id}).to_list(None)
            following_ids = [f["following_id"] for f in follows]
        
        # Get active videos from current competition
        query = {
            "competition_round": current_competition["id"],
            "status": "active",
            "is_paid": True
        }
        
        videos = await self.db.videos.find(query).to_list(None)
        
        # Calculate scores for all videos
        scored_videos = []
        for video_data in videos:
            video = Video(**video_data)
            score = await self.calculate_composite_score(video, current_competition["id"])
            
            # Apply personalization boosts
            final_score = score.total_score
            
            if user_preferences:
                # Boost for followed users
                if video.user_id in following_ids:
                    final_score *= config.follow_boost
                
                # Boost for preferred hashtags
                for hashtag in video.hashtags:
                    if hashtag in user_preferences.preferred_hashtags:
                        final_score *= config.hashtag_boost
                        break
                
                # Reduce for skipped hashtags
                for hashtag in video.hashtags:
                    if hashtag in user_preferences.skipped_hashtags:
                        final_score *= 0.5
                        break
            
            scored_videos.append({
                "video": video.dict(),
                "score": final_score,
                "algorithm_data": score.dict()
            })
        
        # Sort by score
        scored_videos.sort(key=lambda x: x["score"], reverse=True)
        
        # Apply diversity rules
        final_feed = self.apply_diversity_rules(scored_videos, config, limit)
        
        return final_feed
    
    def apply_diversity_rules(self, scored_videos: List[Dict], config: AlgorithmConfig, limit: int) -> List[Dict]:
        """Apply diversity rules to prevent feed from being too repetitive"""
        final_feed = []
        user_video_count = defaultdict(int)
        hashtag_count = defaultdict(int)
        
        for item in scored_videos:
            video = item["video"]
            
            # Check user diversity
            if user_video_count[video["user_id"]] >= config.max_same_user:
                continue
            
            # Check hashtag diversity
            skip_for_hashtag = False
            for hashtag in video["hashtags"]:
                if hashtag_count[hashtag] >= config.max_same_hashtag:
                    skip_for_hashtag = True
                    break
            
            if skip_for_hashtag:
                continue
            
            # Add to feed
            final_feed.append(item)
            user_video_count[video["user_id"]] += 1
            
            for hashtag in video["hashtags"]:
                hashtag_count[hashtag] += 1
            
            # Stop when we have enough
            if len(final_feed) >= limit:
                break
        
        return final_feed
    
    async def update_video_metrics(self, video_id: str, interaction_type: str, value: Optional[float] = None):
        """Update video metrics based on user interactions"""
        
        # Get current video
        video_data = await self.db.videos.find_one({"id": video_id})
        if not video_data:
            return
        
        update_data = {"last_updated": datetime.utcnow()}
        
        if interaction_type == "view":
            update_data["view_count"] = video_data["view_count"] + 1
        elif interaction_type == "like":
            update_data["like_count"] = video_data["like_count"] + 1
        elif interaction_type == "comment":
            update_data["comment_count"] = video_data["comment_count"] + 1
        elif interaction_type == "share":
            update_data["share_count"] = video_data["share_count"] + 1
        elif interaction_type == "watch_time" and value:
            # Update completion and replay rates
            if video_data.get("duration", 0) > 0:
                completion_rate = min(value / video_data["duration"], 1.0)
                if completion_rate > 1.0:  # User replayed
                    replay_rate = completion_rate - 1.0
                    update_data["replay_rate"] = (video_data.get("replay_rate", 0) + replay_rate) / 2
                    update_data["completion_rate"] = 1.0
                else:
                    current_completion = video_data.get("completion_rate", 0)
                    # Moving average of completion rates
                    update_data["completion_rate"] = (current_completion + completion_rate) / 2
        
        # Update engagement rate
        if any(key in update_data for key in ["like_count", "comment_count", "share_count"]):
            total_engagements = (
                video_data.get("like_count", 0) + 
                video_data.get("comment_count", 0) + 
                video_data.get("share_count", 0) * 2
            )
            if video_data.get("view_count", 0) > 0:
                update_data["engagement_rate"] = total_engagements / video_data["view_count"]
        
        await self.db.videos.update_one({"id": video_id}, {"$set": update_data})
    
    async def learn_user_preferences(self, user_id: str, video_id: str, interaction_type: str, value: Optional[float] = None):
        """Learn and update user preferences based on interactions"""
        
        # Get video data for learning
        video_data = await self.db.videos.find_one({"id": video_id})
        if not video_data:
            return
        
        video = Video(**video_data)
        
        # Get or create user preferences
        user_pref_data = await self.db.user_preferences.find_one({"user_id": user_id})
        if user_pref_data:
            user_pref = UserPreference(**user_pref_data)
        else:
            user_pref = UserPreference(user_id=user_id)
        
        # Update preferences based on positive interactions
        if interaction_type in ["like", "comment", "share"]:
            # Learn hashtag preferences
            for hashtag in video.hashtags:
                if hashtag not in user_pref.preferred_hashtags:
                    user_pref.preferred_hashtags.append(hashtag)
                    
                # Remove from skipped if previously skipped
                if hashtag in user_pref.skipped_hashtags:
                    user_pref.skipped_hashtags.remove(hashtag)
            
            # Learn user preferences
            if video.user_id not in user_pref.preferred_users:
                user_pref.preferred_users.append(video.user_id)
        
        elif interaction_type == "watch_time" and value and video.duration:
            # Learn duration preferences
            if value / video.duration < 0.3:  # Watched less than 30%
                # Add hashtags to skipped list
                for hashtag in video.hashtags:
                    if hashtag not in user_pref.skipped_hashtags:
                        user_pref.skipped_hashtags.append(hashtag)
            else:
                # Update preferred duration (moving average)
                if user_pref.preferred_duration:
                    user_pref.preferred_duration = (user_pref.preferred_duration + video.duration) / 2
                else:
                    user_pref.preferred_duration = video.duration
        
        # Update timestamp
        user_pref.updated_at = datetime.utcnow()
        
        # Save preferences
        await self.db.user_preferences.replace_one(
            {"user_id": user_id},
            user_pref.dict(),
            upsert=True
        )