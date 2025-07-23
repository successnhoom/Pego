import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import './App.css';
import PWAInstallPrompt, { PWAUpdatePrompt, OfflineIndicator } from './components/PWAInstallPrompt';
import { usePWA } from './hooks/usePWA';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// TikTok-style Video Feed Component
const TikTokFeed = () => {
  const [videos, setVideos] = useState([]);
  const [currentVideoIndex, setCurrentVideoIndex] = useState(0);
  const [loading, setLoading] = useState(true);
  const [showComments, setShowComments] = useState(false);
  const [showProfile, setShowProfile] = useState(false);
  const [selectedProfile, setSelectedProfile] = useState(null);
  const videoRefs = useRef([]);

  // Mock video data (in real app, fetch from API)
  const mockVideos = [
    {
      id: 1,
      title: "สอนทำอาหารไทย 🍲",
      description: "วิธีทำผัดไทยแบบง่ายๆ ที่บ้าน #ผัดไทย #อาหารไทย #ทำกิน",
      video_url: "https://sample-videos.com/zip/10/mp4/SampleVideo_1280x720_1mb.mp4",
      thumbnail: "https://images.unsplash.com/photo-1565299624946-b28f40a0ca4b?w=300&h=400&fit=crop",
      user: {
        id: 1,
        username: "chef_nong",
        display_name: "เชฟน้อง 👩‍🍳",
        avatar: "https://images.unsplash.com/photo-1494790108755-2616b612b1a8?w=150&h=150&fit=crop&crop=face",
        followers: 15600,
        is_verified: true
      },
      stats: {
        views: 125000,
        likes: 8900,
        comments: 234,
        shares: 67
      },
      is_liked: false,
      is_following: false
    },
    {
      id: 2,
      title: "เต้นคฟเวอร์เพลงฮิต 💃",
      description: "เต้นตาม trend ล่าสุด! ใครเต้นตามได้บ้าง? #เต้น #ฮิต #viral #dance",
      video_url: "https://sample-videos.com/zip/10/mp4/SampleVideo_1280x720_2mb.mp4",
      thumbnail: "https://images.unsplash.com/photo-1508700115892-45ecd05ae2ad?w=300&h=400&fit=crop",
      user: {
        id: 2,
        username: "dance_queen",
        display_name: "เต้นเก่ง 🎭",
        avatar: "https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=150&h=150&fit=crop&crop=face",
        followers: 45200,
        is_verified: false
      },
      stats: {
        views: 340000,
        likes: 23400,
        comments: 1200,
        shares: 890
      },
      is_liked: true,
      is_following: true
    },
    {
      id: 3,
      title: "รีวิวของใหม่ 📱",
      description: "รีวิวโทรศัพท์ใหม่ล่าสุด ดีไหมมาดูกัน! #รีวิว #gadget #โทรศัพท์",
      video_url: "https://sample-videos.com/zip/10/mp4/SampleVideo_1280x720_1mb.mp4",
      thumbnail: "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=300&h=400&fit=crop",
      user: {
        id: 3,
        username: "tech_reviewer",
        display_name: "Tech Master 🔧",
        avatar: "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150&h=150&fit=crop&crop=face",
        followers: 78900,
        is_verified: true
      },
      stats: {
        views: 89000,
        likes: 5600,
        comments: 432,
        shares: 156
      },
      is_liked: false,
      is_following: false
    }
  ];

  useEffect(() => {
    // Simulate API call
    setTimeout(() => {
      setVideos(mockVideos);
      setLoading(false);
    }, 1000);
  }, []);

  // Handle scroll to change videos
  const handleScroll = (e) => {
    const container = e.target;
    const scrollTop = container.scrollTop;
    const itemHeight = window.innerHeight;
    const newIndex = Math.round(scrollTop / itemHeight);
    
    if (newIndex !== currentVideoIndex && newIndex < videos.length) {
      setCurrentVideoIndex(newIndex);
      // Pause previous video, play current video
      videoRefs.current.forEach((video, index) => {
        if (video) {
          if (index === newIndex) {
            video.currentTime = 0;
            video.play();
          } else {
            video.pause();
          }
        }
      });
    }
  };

  const formatNumber = (num) => {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
    return num.toString();
  };

  const handleLike = async (videoId) => {
    // API call to like/unlike video
    setVideos(videos.map(video => 
      video.id === videoId 
        ? { 
            ...video, 
            is_liked: !video.is_liked,
            stats: {
              ...video.stats,
              likes: video.is_liked ? video.stats.likes - 1 : video.stats.likes + 1
            }
          }
        : video
    ));
  };

  const handleFollow = async (userId) => {
    setVideos(videos.map(video => 
      video.user.id === userId 
        ? { ...video, is_following: !video.is_following }
        : video
    ));
  };

  const handleShare = async (video) => {
    if (navigator.share) {
      try {
        await navigator.share({
          title: video.title,
          text: video.description,
          url: window.location.href
        });
      } catch (error) {
        console.log('Error sharing:', error);
      }
    } else {
      // Fallback: copy to clipboard
      navigator.clipboard.writeText(window.location.href);
      alert('ลิงก์ถูกคัดลอกแล้ว!');
    }
  };

  const openComments = (videoId) => {
    setShowComments(true);
  };

  const openProfile = (user) => {
    setSelectedProfile(user);
    setShowProfile(true);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-black">
        <div className="spinner border-white"></div>
      </div>
    );
  }

  return (
    <div className="relative h-screen bg-black overflow-hidden">
      {/* Video Container */}
      <div 
        className="h-full overflow-y-scroll snap-y snap-mandatory hide-scrollbar"
        onScroll={handleScroll}
        style={{ scrollBehavior: 'smooth' }}
      >
        {videos.map((video, index) => (
          <div 
            key={video.id} 
            className="relative h-screen snap-start flex items-center justify-center bg-black"
          >
            {/* Video Player */}
            <video
              ref={el => videoRefs.current[index] = el}
              className="w-full h-full object-cover"
              loop
              muted
              playsInline
              poster={video.thumbnail}
              onPlay={() => setCurrentVideoIndex(index)}
            >
              <source src={video.video_url} type="video/mp4" />
            </video>

            {/* Video Overlay Controls */}
            <div className="absolute inset-0 flex">
              {/* Left side - Video info */}
              <div className="flex-1 flex flex-col justify-end p-4 pb-20">
                {/* User info */}
                <div className="flex items-center mb-3">
                  <img
                    src={video.user.avatar}
                    alt={video.user.display_name}
                    className="w-12 h-12 rounded-full border-2 border-white mr-3 cursor-pointer"
                    onClick={() => openProfile(video.user)}
                  />
                  <div className="flex-1">
                    <div className="flex items-center">
                      <span 
                        className="text-white font-semibold cursor-pointer hover:underline"
                        onClick={() => openProfile(video.user)}
                      >
                        {video.user.display_name}
                      </span>
                      {video.user.is_verified && (
                        <span className="text-blue-400 ml-1">✓</span>
                      )}
                    </div>
                    <p className="text-gray-300 text-sm">@{video.user.username}</p>
                  </div>
                  {!video.is_following && (
                    <button
                      onClick={() => handleFollow(video.user.id)}
                      className="bg-red-500 text-white px-4 py-1 rounded-full text-sm font-semibold hover:bg-red-600 transition-colors"
                    >
                      ติดตาม
                    </button>
                  )}
                </div>

                {/* Video title & description */}
                <h3 className="text-white font-semibold text-lg mb-2">{video.title}</h3>
                <p className="text-white text-sm mb-2 line-clamp-2">{video.description}</p>
                
                {/* View count */}
                <div className="flex items-center text-gray-300 text-sm">
                  <span className="mr-4">👁 {formatNumber(video.stats.views)} ครั้ง</span>
                </div>
              </div>

              {/* Right side - Action buttons */}
              <div className="w-16 flex flex-col justify-end items-center pb-20 space-y-6">
                {/* Like button */}
                <div className="flex flex-col items-center">
                  <button
                    onClick={() => handleLike(video.id)}
                    className={`w-12 h-12 rounded-full flex items-center justify-center transition-all ${
                      video.is_liked 
                        ? 'bg-red-500 text-white scale-110' 
                        : 'bg-black bg-opacity-50 text-white hover:scale-110'
                    }`}
                  >
                    <span className="text-2xl">
                      {video.is_liked ? '❤️' : '🤍'}
                    </span>
                  </button>
                  <span className="text-white text-xs mt-1">
                    {formatNumber(video.stats.likes)}
                  </span>
                </div>

                {/* Comment button */}
                <div className="flex flex-col items-center">
                  <button
                    onClick={() => openComments(video.id)}
                    className="w-12 h-12 rounded-full bg-black bg-opacity-50 text-white flex items-center justify-center hover:scale-110 transition-all"
                  >
                    <span className="text-2xl">💬</span>
                  </button>
                  <span className="text-white text-xs mt-1">
                    {formatNumber(video.stats.comments)}
                  </span>
                </div>

                {/* Share button */}
                <div className="flex flex-col items-center">
                  <button
                    onClick={() => handleShare(video)}
                    className="w-12 h-12 rounded-full bg-black bg-opacity-50 text-white flex items-center justify-center hover:scale-110 transition-all"
                  >
                    <span className="text-2xl">📤</span>
                  </button>
                  <span className="text-white text-xs mt-1">
                    {formatNumber(video.stats.shares)}
                  </span>
                </div>

                {/* Prize indicator for competition */}
                <div className="flex flex-col items-center">
                  <div className="w-12 h-12 rounded-full bg-yellow-500 bg-opacity-80 text-white flex items-center justify-center">
                    <span className="text-2xl">🏆</span>
                  </div>
                  <span className="text-yellow-300 text-xs mt-1 text-center">
                    30฿
                  </span>
                </div>
              </div>
            </div>

            {/* Scroll indicator */}
            {index < videos.length - 1 && (
              <div className="absolute bottom-4 left-1/2 transform -translate-x-1/2 text-white text-opacity-60 animate-bounce">
                <span className="text-2xl">⬇</span>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Comments Modal */}
      {showComments && (
        <CommentsModal
          onClose={() => setShowComments(false)}
          videoId={videos[currentVideoIndex]?.id}
        />
      )}

      {/* Profile Modal */}
      {showProfile && selectedProfile && (
        <ProfileModal
          user={selectedProfile}
          onClose={() => setShowProfile(false)}
        />
      )}
    </div>
  );
};

// Comments Modal Component
const CommentsModal = ({ onClose, videoId }) => {
  const [comments, setComments] = useState([]);
  const [newComment, setNewComment] = useState('');

  // Mock comments
  const mockComments = [
    {
      id: 1,
      user: {
        username: "foodie_lover",
        avatar: "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=50&h=50&fit=crop&crop=face"
      },
      text: "สอนได้เก่งมาก! จะลองทำตามค่ะ 👍",
      likes: 23,
      time: "2 ชม."
    },
    {
      id: 2,
      user: {
        username: "cooking_mom",
        avatar: "https://images.unsplash.com/photo-1580489944761-15a19d654956?w=50&h=50&fit=crop&crop=face"
      },
      text: "เด็ดจริง! ลูกชอบมาก ขอบคุณค่ะ",
      likes: 45,
      time: "1 ชม."
    }
  ];

  useEffect(() => {
    setComments(mockComments);
  }, [videoId]);

  const handleSubmitComment = (e) => {
    e.preventDefault();
    if (newComment.trim()) {
      const comment = {
        id: Date.now(),
        user: {
          username: "current_user",
          avatar: "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=50&h=50&fit=crop&crop=face"
        },
        text: newComment,
        likes: 0,
        time: "ตอนนี้"
      };
      setComments([comment, ...comments]);
      setNewComment('');
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-75 z-50 flex items-end">
      <div className="bg-white w-full h-3/4 rounded-t-3xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b">
          <h3 className="font-semibold text-lg">ความเห็น</h3>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center"
          >
            ✕
          </button>
        </div>

        {/* Comments list */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4" style={{ height: 'calc(75vh - 140px)' }}>
          {comments.map(comment => (
            <div key={comment.id} className="flex space-x-3">
              <img
                src={comment.user.avatar}
                alt={comment.user.username}
                className="w-8 h-8 rounded-full"
              />
              <div className="flex-1">
                <div className="flex items-center space-x-2">
                  <span className="font-medium text-sm">{comment.user.username}</span>
                  <span className="text-gray-500 text-xs">{comment.time}</span>
                </div>
                <p className="text-sm mt-1">{comment.text}</p>
                <div className="flex items-center space-x-4 mt-2">
                  <button className="text-gray-500 text-xs hover:text-red-500">
                    ❤️ {comment.likes}
                  </button>
                  <button className="text-gray-500 text-xs">ตอบกลับ</button>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Comment input */}
        <form onSubmit={handleSubmitComment} className="p-4 border-t bg-gray-50">
          <div className="flex space-x-2">
            <input
              type="text"
              value={newComment}
              onChange={(e) => setNewComment(e.target.value)}
              placeholder="แสดงความเห็น..."
              className="flex-1 px-3 py-2 border rounded-full focus:outline-none focus:border-purple-500"
            />
            <button
              type="submit"
              className="px-4 py-2 bg-purple-600 text-white rounded-full hover:bg-purple-700 transition-colors"
            >
              ส่ง
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// Profile Modal Component
const ProfileModal = ({ user, onClose }) => {
  const [isFollowing, setIsFollowing] = useState(user.is_following || false);
  const [userVideos] = useState([
    { id: 1, thumbnail: "https://images.unsplash.com/photo-1565299624946-b28f40a0ca4b?w=150&h=200&fit=crop", views: "125K" },
    { id: 2, thumbnail: "https://images.unsplash.com/photo-1565299507177-b0ac66763e45?w=150&h=200&fit=crop", views: "89K" },
    { id: 3, thumbnail: "https://images.unsplash.com/photo-1565299585323-38174c0f6efe?w=150&h=200&fit=crop", views: "67K" },
  ]);

  const handleFollow = () => {
    setIsFollowing(!isFollowing);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-75 z-50 flex items-center justify-center">
      <div className="bg-white w-full max-w-md h-5/6 rounded-3xl overflow-hidden">
        {/* Header */}
        <div className="relative">
          <div className="h-32 bg-gradient-to-r from-purple-600 to-pink-600"></div>
          <button
            onClick={onClose}
            className="absolute top-4 right-4 w-8 h-8 rounded-full bg-black bg-opacity-50 text-white flex items-center justify-center"
          >
            ✕
          </button>
          
          {/* Profile info */}
          <div className="relative px-4 pb-4">
            <div className="relative -mt-16 mb-4">
              <img
                src={user.avatar}
                alt={user.display_name}
                className="w-24 h-24 rounded-full border-4 border-white mx-auto"
              />
            </div>
            
            <div className="text-center">
              <div className="flex items-center justify-center">
                <h2 className="text-xl font-bold">{user.display_name}</h2>
                {user.is_verified && (
                  <span className="text-blue-500 ml-1">✓</span>
                )}
              </div>
              <p className="text-gray-600">@{user.username}</p>
              
              {/* Stats */}
              <div className="flex justify-center space-x-6 mt-4">
                <div className="text-center">
                  <div className="font-bold text-lg">{(user.followers / 1000).toFixed(1)}K</div>
                  <div className="text-gray-600 text-sm">ผู้ติดตาม</div>
                </div>
                <div className="text-center">
                  <div className="font-bold text-lg">156</div>
                  <div className="text-gray-600 text-sm">กำลังติดตาม</div>
                </div>
                <div className="text-center">
                  <div className="font-bold text-lg">2.1M</div>
                  <div className="text-gray-600 text-sm">ถูกใจ</div>
                </div>
              </div>

              {/* Follow button */}
              <button
                onClick={handleFollow}
                className={`mt-4 px-8 py-2 rounded-full font-semibold transition-colors ${
                  isFollowing
                    ? 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                    : 'bg-purple-600 text-white hover:bg-purple-700'
                }`}
              >
                {isFollowing ? 'กำลังติดตาม' : 'ติดตาม'}
              </button>
            </div>
          </div>
        </div>

        {/* User Videos Grid */}
        <div className="p-4">
          <h3 className="font-semibold mb-3">วิดีโอ</h3>
          <div className="grid grid-cols-3 gap-2">
            {userVideos.map(video => (
              <div key={video.id} className="relative aspect-video bg-gray-200 rounded-lg overflow-hidden">
                <img
                  src={video.thumbnail}
                  alt="Video thumbnail"
                  className="w-full h-full object-cover"
                />
                <div className="absolute bottom-1 right-1 bg-black bg-opacity-70 text-white text-xs px-1 rounded">
                  👁 {video.views}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

// Enhanced Upload Component for TikTok style
const EnhancedVideoUpload = () => {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [hashtags, setHashtags] = useState('');
  const [userId, setUserId] = useState('');
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [message, setMessage] = useState('');
  const [step, setStep] = useState(1); // 1: form, 2: payment selection, 3: payment processing
  const [videoId, setVideoId] = useState('');
  const [paymentMethods, setPaymentMethods] = useState([]);
  const [selectedPaymentMethod, setSelectedPaymentMethod] = useState('');
  const [paymentSession, setPaymentSession] = useState(null);

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      setSelectedFile(file);
      const url = URL.createObjectURL(file);
      setPreviewUrl(url);
    }
  };

  const handleInitiateUpload = async (e) => {
    e.preventDefault();
    if (!title || !selectedFile || !userId) {
      setMessage('กรุณากรอกข้อมูลให้ครบถ้วน');
      return;
    }

    setIsUploading(true);
    setMessage('กำลังเตรียมข้อมูล...');

    try {
      // Step 1: Initiate video upload
      const uploadResponse = await axios.post(`${API}/upload/initiate`, {
        title,
        description: `${description} ${hashtags}`,
        user_id: userId
      });

      setVideoId(uploadResponse.data.video_id);

      // Step 2: Get payment methods
      const methodsResponse = await axios.get(`${API}/payment/methods`);
      setPaymentMethods(methodsResponse.data.payment_methods);
      
      setStep(2);
      setMessage('');
      setIsUploading(false);

    } catch (error) {
      setMessage('เกิดข้อผิดพลาด: ' + error.response?.data?.detail || error.message);
      setIsUploading(false);
    }
  };

  const handlePaymentMethodSelection = async (methodId) => {
    setSelectedPaymentMethod(methodId);
    setIsUploading(true);
    setMessage('กำลังสร้างการชำระเงิน...');

    try {
      const paymentResponse = await axios.post(`${API}/payment/create`, {
        video_id: videoId,
        payment_method: methodId,
        user_id: userId
      });

      setPaymentSession(paymentResponse.data);
      setStep(3);
      setMessage('');

      if (methodId === 'stripe') {
        // Redirect to Stripe checkout
        window.location.href = paymentResponse.data.checkout_url;
      } else if (methodId === 'promptpay') {
        // Show PromptPay QR code
        setIsUploading(false);
      }

    } catch (error) {
      setMessage('เกิดข้อผิดพลาด: ' + error.response?.data?.detail || error.message);
      setIsUploading(false);
    }
  };

  const handlePromptPayConfirm = async () => {
    setIsUploading(true);
    setMessage('กำลังยืนยันการชำระเงิน...');

    try {
      await axios.post(`${API}/payment/confirm/promptpay/${paymentSession.session_id}`);
      setMessage('✅ ชำระเงินสำเร็จ! กำลังดำเนินการอัพโหลดวิดีโอ...');
      
      // Upload video file
      const formData = new FormData();
      formData.append('file', selectedFile);

      await axios.post(`${API}/upload/video/${videoId}`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        }
      });

      setMessage('🎉 อัพโหลดวิดีโอสำเร็จ!');
      setTimeout(() => {
        setStep(1);
        setTitle('');
        setDescription('');
        setHashtags('');
        setUserId('');
        setSelectedFile(null);
        setPreviewUrl('');
        setMessage('');
        setVideoId('');
        setPaymentSession(null);
      }, 3000);

    } catch (error) {
      setMessage('เกิดข้อผิดพลาด: ' + error.response?.data?.detail || error.message);
    } finally {
      setIsUploading(false);
    }
  };

  const renderStep = () => {
    switch (step) {
      case 1:
        return (
          <form onSubmit={handleInitiateUpload} className="space-y-6">
            {/* Video Preview */}
            {previewUrl && (
              <div className="relative aspect-video bg-gray-800 rounded-lg overflow-hidden">
                <video
                  src={previewUrl}
                  className="w-full h-full object-cover"
                  controls
                  muted
                />
              </div>
            )}

            {/* File Upload */}
            <div>
              <label className="block text-sm font-medium mb-2">เลือกวิดีโอ</label>
              <input
                type="file"
                accept="video/*"
                onChange={handleFileSelect}
                className="w-full p-3 bg-gray-800 border border-gray-600 rounded-lg text-white file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-purple-600 file:text-white hover:file:bg-purple-700"
              />
            </div>

            {/* Title */}
            <div>
              <label className="block text-sm font-medium mb-2">หัวข้อวิดีโอ</label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                className="w-full p-3 bg-gray-800 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                placeholder="เช่น สอนทำอาหารไทย"
              />
            </div>

            {/* Description */}
            <div>
              <label className="block text-sm font-medium mb-2">คำอธิบาย</label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows="3"
                className="w-full p-3 bg-gray-800 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                placeholder="อธิบายเนื้อหาในวิดีโอ..."
              />
            </div>

            {/* Hashtags */}
            <div>
              <label className="block text-sm font-medium mb-2">แฮชแท็ก</label>
              <input
                type="text"
                value={hashtags}
                onChange={(e) => setHashtags(e.target.value)}
                className="w-full p-3 bg-gray-800 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                placeholder="#อาหาร #ทำกิน #สูตรลับ"
              />
            </div>

            {/* User ID */}
            <div>
              <label className="block text-sm font-medium mb-2">User ID</label>
              <input
                type="text"
                value={userId}
                onChange={(e) => setUserId(e.target.value)}
                className="w-full p-3 bg-gray-800 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                placeholder="กรอก User ID ของคุณ"
              />
            </div>

            {/* Competition Info */}
            <div className="bg-gradient-to-r from-purple-900 to-pink-900 p-4 rounded-lg">
              <h3 className="font-bold text-lg mb-2">🏆 การแข่งขันวิดีโอ</h3>
              <div className="space-y-1 text-sm">
                <p>💰 ค่าสมัคร: 30 บาท</p>
                <p>🥇 Top 1,000 วิดีโอได้รับ 70% ของเงินรางวัล</p>
                <p>⏰ รอบการแข่งขัน: 7 วัน</p>
                <p>📊 อันดับตามจำนวนการดู</p>
              </div>
            </div>

            <button
              type="submit"
              disabled={isUploading}
              className={`w-full py-4 px-4 rounded-lg font-bold text-lg transition-all ${
                isUploading
                  ? 'bg-gray-600 cursor-not-allowed'
                  : 'bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 shadow-lg hover:shadow-xl'
              }`}
            >
              {isUploading ? 'กำลังดำเนินการ...' : '📝 ถัดไป - เลือกวิธีชำระเงิน'}
            </button>
          </form>
        );

      case 2:
        return (
          <div className="space-y-6">
            <div className="text-center">
              <h3 className="text-2xl font-bold mb-2">เลือกวิธีชำระเงิน</h3>
              <p className="text-gray-400">ค่าสมัครการแข่งขัน 30 บาท</p>
            </div>

            <div className="space-y-4">
              {paymentMethods.map((method) => (
                <button
                  key={method.id}
                  onClick={() => handlePaymentMethodSelection(method.id)}
                  disabled={isUploading}
                  className={`w-full p-4 rounded-lg border-2 transition-all ${
                    selectedPaymentMethod === method.id
                      ? 'border-purple-500 bg-purple-900'
                      : 'border-gray-600 hover:border-purple-400'
                  } ${isUploading ? 'opacity-50 cursor-not-allowed' : ''}`}
                >
                  <div className="flex items-center space-x-4">
                    <div className="text-3xl">{method.icon}</div>
                    <div className="flex-1 text-left">
                      <h4 className="font-bold">{method.name}</h4>
                      <p className="text-sm text-gray-400">{method.description}</p>
                    </div>
                    <div className="text-purple-400">→</div>
                  </div>
                </button>
              ))}
            </div>

            <button
              onClick={() => setStep(1)}
              className="w-full py-3 px-4 rounded-lg border border-gray-600 text-gray-400 hover:text-white hover:border-gray-400 transition-all"
            >
              ← กลับไปแก้ไขข้อมูล
            </button>
          </div>
        );

      case 3:
        if (selectedPaymentMethod === 'promptpay') {
          return (
            <div className="space-y-6">
              <div className="text-center">
                <h3 className="text-2xl font-bold mb-2">ชำระเงินผ่าน PromptPay</h3>
                <p className="text-gray-400">สแกน QR Code เพื่อชำระเงิน 30 บาท</p>
              </div>

              {paymentSession && (
                <div className="bg-white p-6 rounded-lg">
                  <img
                    src={paymentSession.qr_code}
                    alt="PromptPay QR Code"
                    className="w-full max-w-sm mx-auto"
                  />
                </div>
              )}

              <div className="text-center text-sm text-gray-400">
                <p>สแกน QR Code ด้วยแอปธนาคารของคุณ</p>
                <p>หรือแอป PromptPay อื่นๆ</p>
              </div>

              <button
                onClick={handlePromptPayConfirm}
                disabled={isUploading}
                className={`w-full py-4 px-4 rounded-lg font-bold text-lg transition-all ${
                  isUploading
                    ? 'bg-gray-600 cursor-not-allowed'
                    : 'bg-green-600 hover:bg-green-700 shadow-lg hover:shadow-xl'
                }`}
              >
                {isUploading ? 'กำลังยืนยัน...' : '✅ ยืนยันการชำระเงินแล้ว'}
              </button>

              <button
                onClick={() => setStep(2)}
                className="w-full py-3 px-4 rounded-lg border border-gray-600 text-gray-400 hover:text-white hover:border-gray-400 transition-all"
              >
                ← เปลี่ยนวิธีชำระเงิน
              </button>
            </div>
          );
        }

        return (
          <div className="text-center space-y-4">
            <div className="text-6xl">🔄</div>
            <h3 className="text-2xl font-bold">กำลังประมวลผล...</h3>
            <p className="text-gray-400">กำลังเปลี่ยนเส้นทางไปยังหน้าชำระเงิน</p>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-black text-white p-4">
      <div className="max-w-md mx-auto">
        <h2 className="text-2xl font-bold text-center mb-6">สร้างวิดีโอ 🎬</h2>
        
        {renderStep()}

        {message && (
          <div className={`mt-4 p-3 rounded-lg ${
            message.includes('สำเร็จ') || message.includes('✅') || message.includes('🎉')
              ? 'bg-green-900 text-green-200 border border-green-700'
              : message.includes('ข้อผิดพลาด')
              ? 'bg-red-900 text-red-200 border border-red-700'
              : 'bg-blue-900 text-blue-200 border border-blue-700'
          }`}>
            {message}
          </div>
        )}
      </div>
    </div>
  );
};

// Navigation Component
const TikTokNavigation = ({ currentView, setCurrentView }) => {
  const navItems = [
    { key: 'feed', icon: '🏠', label: 'หน้าหลัก' },
    { key: 'discover', icon: '🔍', label: 'ค้นหา' },
    { key: 'upload', icon: '➕', label: 'สร้าง', special: true },
    { key: 'inbox', icon: '💬', label: 'กล่องข้อความ' },
    { key: 'profile', icon: '👤', label: 'โปรไฟล์' }
  ];

  return (
    <nav className="fixed bottom-0 left-0 right-0 bg-black border-t border-gray-800 z-50">
      <div className="flex justify-around items-center py-2">
        {navItems.map(item => (
          <button
            key={item.key}
            onClick={() => setCurrentView(item.key)}
            className={`flex flex-col items-center justify-center transition-all ${
              item.special
                ? 'bg-gradient-to-r from-purple-600 to-pink-600 rounded-xl p-2 transform scale-110'
                : currentView === item.key
                ? 'text-white scale-110'
                : 'text-gray-500 hover:text-white'
            }`}
          >
            <span className={`text-2xl ${item.special ? 'text-white' : ''}`}>
              {item.icon}
            </span>
            <span className={`text-xs mt-1 ${item.special ? 'text-white' : ''}`}>
              {item.label}
            </span>
          </button>
        ))}
      </div>
    </nav>
  );
};

// Main App Component
const App = () => {
  const [currentView, setCurrentView] = useState('feed');
  const { isInstalled, isOnline } = usePWA();

  // Check URL parameters for direct navigation
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('session_id')) {
      setCurrentView('payment-success');
    }
  }, []);

  const renderContent = () => {
    switch (currentView) {
      case 'feed':
        return <TikTokFeed />;
      case 'discover':
        return (
          <div className="h-screen bg-black text-white flex items-center justify-center">
            <div className="text-center">
              <div className="text-6xl mb-4">🔍</div>
              <h2 className="text-2xl font-bold">ค้นหา</h2>
              <p className="text-gray-400 mt-2">ฟีเจอร์กำลังพัฒนา</p>
            </div>
          </div>
        );
      case 'upload':
        return <EnhancedVideoUpload />;
      case 'inbox':
        return (
          <div className="h-screen bg-black text-white flex items-center justify-center">
            <div className="text-center">
              <div className="text-6xl mb-4">💬</div>
              <h2 className="text-2xl font-bold">กล่องข้อความ</h2>
              <p className="text-gray-400 mt-2">ฟีเจอร์กำลังพัฒนา</p>
            </div>
          </div>
        );
      case 'profile':
        return (
          <div className="h-screen bg-black text-white flex items-center justify-center">
            <div className="text-center">
              <div className="text-6xl mb-4">👤</div>
              <h2 className="text-2xl font-bold">โปรไฟล์</h2>
              <p className="text-gray-400 mt-2">ฟีเจอร์กำลังพัฒนา</p>
            </div>
          </div>
        );
      default:
        return <TikTokFeed />;
    }
  };

  return (
    <div className="h-screen bg-black overflow-hidden">
      {/* PWA Components */}
      <OfflineIndicator />
      <PWAUpdatePrompt />
      
      {/* Main Content */}
      {renderContent()}

      {/* Bottom Navigation */}
      <TikTokNavigation currentView={currentView} setCurrentView={setCurrentView} />

      {/* PWA Install Prompt */}
      <PWAInstallPrompt />
    </div>
  );
};

export default App;