import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import axios from 'axios';

const ProfilePage = ({ userId = null }) => {
  const { user, isAuthenticated, updateProfile } = useAuth();
  const [profileData, setProfileData] = useState(null);
  const [userVideos, setUserVideos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isEditing, setIsEditing] = useState(false);
  const [editForm, setEditForm] = useState({
    display_name: '',
    bio: '',
    username: ''
  });
  const [activeTab, setActiveTab] = useState('videos'); // 'videos', 'liked'
  const [followStats, setFollowStats] = useState({
    isFollowing: false,
    followersCount: 0,
    followingCount: 0
  });

  const API_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001/api';
  const isOwnProfile = !userId || (user && userId === user.id);

  useEffect(() => {
    loadProfileData();
  }, [userId]);

  const loadProfileData = async () => {
    try {
      setLoading(true);
      
      if (isOwnProfile && user) {
        // Load own profile
        setProfileData(user);
        setEditForm({
          display_name: user.display_name || '',
          bio: user.bio || '',
          username: user.username || ''
        });
      } else if (userId) {
        // Load other user's profile
        const response = await axios.get(`${API_URL}/users/${userId}`);
        setProfileData(response.data.user);
        setFollowStats({
          isFollowing: response.data.is_following,
          followersCount: response.data.user.followers_count,
          followingCount: response.data.user.following_count
        });
      }

      // Load user videos (mock data for now)
      setUserVideos([
        {
          id: 1,
          title: "วิดีโอแรกของฉัน",
          thumbnail: "🎬",
          views: 1200,
          likes: 89,
          duration: "0:45"
        },
        {
          id: 2,
          title: "เต้นเพลงฮิต",
          thumbnail: "💃",
          views: 3400,
          likes: 234,
          duration: "1:20"
        },
        {
          id: 3,
          title: "รีวิวอาหาร",
          thumbnail: "🍜",
          views: 890,
          likes: 67,
          duration: "2:15"
        }
      ]);

    } catch (error) {
      console.error('Failed to load profile:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleEditSubmit = async (e) => {
    e.preventDefault();
    const result = await updateProfile(editForm);
    if (result.success) {
      setProfileData(result.user);
      setIsEditing(false);
    }
  };

  const handleFollow = async () => {
    if (!isAuthenticated) return;
    
    try {
      // Mock follow/unfollow
      setFollowStats(prev => ({
        ...prev,
        isFollowing: !prev.isFollowing,
        followersCount: prev.isFollowing ? prev.followersCount - 1 : prev.followersCount + 1
      }));
    } catch (error) {
      console.error('Follow failed:', error);
    }
  };

  const formatNumber = (num) => {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
    return num.toString();
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-black text-white flex items-center justify-center">
        <div className="text-center">
          <div className="text-6xl mb-4">⏳</div>
          <p className="text-gray-400">กำลังโหลด...</p>
        </div>
      </div>
    );
  }

  if (!profileData) {
    return (
      <div className="min-h-screen bg-black text-white flex items-center justify-center">
        <div className="text-center">
          <div className="text-6xl mb-4">❌</div>
          <h2 className="text-xl font-bold mb-2">ไม่พบโปรไฟล์</h2>
          <p className="text-gray-400">ผู้ใช้ที่คุณค้นหาไม่พบ</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-black text-white">
      {/* Profile Header */}
      <div className="px-4 py-6">
        {/* Profile Picture & Basic Info */}
        <div className="flex items-start space-x-4 mb-6">
          <div className="w-24 h-24 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full flex items-center justify-center text-white font-bold text-3xl flex-shrink-0">
            {profileData.avatar_url ? (
              <img src={profileData.avatar_url} alt="Profile" className="w-full h-full rounded-full object-cover" />
            ) : (
              profileData.display_name?.charAt(0) || 'U'
            )}
          </div>

          <div className="flex-1 min-w-0">
            <div className="flex items-center space-x-2 mb-2">
              <h1 className="text-xl font-bold truncate">{profileData.display_name}</h1>
              {profileData.is_verified && (
                <span className="text-blue-400 text-lg">✓</span>
              )}
            </div>
            <p className="text-gray-400 text-sm mb-2">@{profileData.username}</p>
            
            {/* Stats */}
            <div className="flex space-x-6 text-sm">
              <div className="text-center">
                <div className="font-bold text-white">{formatNumber(followStats.followingCount || 0)}</div>
                <div className="text-gray-400">กำลังติดตาม</div>
              </div>
              <div className="text-center">
                <div className="font-bold text-white">{formatNumber(followStats.followersCount || 0)}</div>
                <div className="text-gray-400">ผู้ติดตาม</div>
              </div>
              <div className="text-center">
                <div className="font-bold text-white">{formatNumber(profileData.total_likes || 0)}</div>
                <div className="text-gray-400">ถูกใจ</div>
              </div>
            </div>
          </div>
        </div>

        {/* Bio */}
        {profileData.bio && (
          <div className="mb-4">
            <p className="text-gray-300 text-sm leading-relaxed">{profileData.bio}</p>
          </div>
        )}

        {/* Credits Display (for own profile) */}
        {isOwnProfile && (
          <div className="bg-gradient-to-r from-yellow-600 to-orange-600 rounded-lg p-3 mb-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <span className="text-lg">💰</span>
                <span className="font-bold">เครดิต: {profileData.credits || 0}</span>
              </div>
              <div className="text-xs text-yellow-100">
                อัพโหลดได้ {Math.floor((profileData.credits || 0) / 30)} คลิป
              </div>
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex space-x-3 mb-6">
          {isOwnProfile ? (
            <>
              <button
                onClick={() => setIsEditing(true)}
                className="flex-1 bg-gray-700 hover:bg-gray-600 py-2 px-4 rounded-lg font-medium transition-all"
              >
                แก้ไขโปรไฟล์
              </button>
              <button className="flex-1 bg-gray-700 hover:bg-gray-600 py-2 px-4 rounded-lg font-medium transition-all">
                แชร์โปรไฟล์
              </button>
            </>
          ) : (
            <>
              <button
                onClick={handleFollow}
                className={`flex-1 py-2 px-4 rounded-lg font-medium transition-all ${
                  followStats.isFollowing
                    ? 'bg-gray-700 hover:bg-gray-600 text-white'
                    : 'bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white'
                }`}
              >
                {followStats.isFollowing ? 'กำลังติดตาม' : 'ติดตาม'}
              </button>
              <button className="bg-gray-700 hover:bg-gray-600 py-2 px-4 rounded-lg font-medium transition-all">
                💬
              </button>
              <button className="bg-gray-700 hover:bg-gray-600 py-2 px-4 rounded-lg font-medium transition-all">
                📤
              </button>
            </>
          )}
        </div>

        {/* Tabs */}
        <div className="flex border-b border-gray-700">
          <button
            onClick={() => setActiveTab('videos')}
            className={`flex-1 py-3 text-center font-medium transition-all ${
              activeTab === 'videos'
                ? 'text-white border-b-2 border-white'
                : 'text-gray-400 hover:text-gray-300'
            }`}
          >
            📹 วิดีโอ
          </button>
          <button
            onClick={() => setActiveTab('liked')}
            className={`flex-1 py-3 text-center font-medium transition-all ${
              activeTab === 'liked'
                ? 'text-white border-b-2 border-white'
                : 'text-gray-400 hover:text-gray-300'
            }`}
          >
            ❤️ ถูกใจ
          </button>
        </div>
      </div>

      {/* Video Grid */}
      <div className="px-4 pb-6">
        {activeTab === 'videos' && (
          <div className="grid grid-cols-3 gap-1">
            {userVideos.map((video) => (
              <div key={video.id} className="aspect-[9/16] bg-gray-800 rounded-lg relative overflow-hidden">
                <div className="absolute inset-0 flex items-center justify-center text-4xl">
                  {video.thumbnail}
                </div>
                <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black to-transparent p-2">
                  <div className="text-xs font-medium truncate">{video.title}</div>
                  <div className="flex items-center justify-between text-xs text-gray-300 mt-1">
                    <span>👁️ {formatNumber(video.views)}</span>
                    <span>{video.duration}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {activeTab === 'liked' && (
          <div className="text-center py-12">
            <div className="text-6xl mb-4">❤️</div>
            <h3 className="text-xl font-bold mb-2">วิดีโอที่ถูกใจ</h3>
            <p className="text-gray-400">วิดีโอที่คุณกดถูกใจจะแสดงที่นี่</p>
          </div>
        )}
      </div>

      {/* Edit Profile Modal */}
      {isEditing && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-gray-900 rounded-lg max-w-md w-full p-6">
            <h2 className="text-xl font-bold mb-4">แก้ไขโปรไฟล์</h2>
            
            <form onSubmit={handleEditSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">ชื่อที่แสดง</label>
                <input
                  type="text"
                  value={editForm.display_name}
                  onChange={(e) => setEditForm({...editForm, display_name: e.target.value})}
                  className="w-full p-3 bg-gray-800 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-purple-500"
                  placeholder="ชื่อของคุณ"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">ชื่อผู้ใช้</label>
                <input
                  type="text"
                  value={editForm.username}
                  onChange={(e) => setEditForm({...editForm, username: e.target.value})}
                  className="w-full p-3 bg-gray-800 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-purple-500"
                  placeholder="username"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">เกี่ยวกับ</label>
                <textarea
                  rows="3"
                  value={editForm.bio}
                  onChange={(e) => setEditForm({...editForm, bio: e.target.value})}
                  className="w-full p-3 bg-gray-800 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-purple-500"
                  placeholder="เขียนบางอย่างเกี่ยวกับคุณ..."
                />
              </div>

              <div className="flex space-x-3">
                <button
                  type="button"
                  onClick={() => setIsEditing(false)}
                  className="flex-1 py-3 px-4 rounded-lg border border-gray-600 text-gray-400 hover:text-white hover:border-gray-400 transition-all"
                >
                  ยกเลิก
                </button>
                <button
                  type="submit"
                  className="flex-1 py-3 px-4 rounded-lg bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white font-medium transition-all"
                >
                  บันทึก
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default ProfilePage;