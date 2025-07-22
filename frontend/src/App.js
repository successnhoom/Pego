import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Video Upload Component
const VideoUpload = ({ onUploadSuccess }) => {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [userId, setUserId] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [message, setMessage] = useState('');

  const handleInitiateUpload = async (e) => {
    e.preventDefault();
    if (!title || !userId) {
      setMessage('กรุณาใส่ชื่อวิดีโอและ User ID');
      return;
    }

    setIsUploading(true);
    setMessage('กำลังเตรียมการชำระเงิน...');

    try {
      const response = await axios.post(`${API}/upload/initiate`, {
        title,
        description,
        user_id: userId
      });

      // Redirect to payment
      window.location.href = response.data.checkout_url;

    } catch (error) {
      setMessage('เกิดข้อผิดพลาด: ' + error.response?.data?.detail || error.message);
      setIsUploading(false);
    }
  };

  return (
    <div className="max-w-md mx-auto bg-white rounded-xl shadow-md p-6">
      <h2 className="text-2xl font-bold text-center mb-6 text-purple-600">อัพโหลดวิดีโอ</h2>
      <form onSubmit={handleInitiateUpload} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            ชื่อวิดีโอ *
          </label>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
            placeholder="ใส่ชื่อวิดีโอของคุณ"
            maxLength={100}
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            คำอธิบาย
          </label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
            placeholder="อธิบายเกี่ยวกับวิดีโอ"
            rows={3}
            maxLength={500}
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            User ID *
          </label>
          <input
            type="text"
            value={userId}
            onChange={(e) => setUserId(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
            placeholder="ใส่ User ID ของคุณ"
          />
        </div>
        <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4">
          <p className="text-sm text-yellow-800">
            💰 ค่าอัพโหลด: <span className="font-bold">30 บาท</span> ต่อวิดีโอ<br/>
            📹 ความยาวสูงสุด: 3 นาที<br/>
            🏆 วิดีโอ Top 1,000 ได้รับรางวัล!
          </p>
        </div>
        <button
          type="submit"
          disabled={isUploading}
          className={`w-full py-3 px-4 rounded-md font-medium ${
            isUploading
              ? 'bg-gray-400 cursor-not-allowed'
              : 'bg-purple-600 hover:bg-purple-700 text-white'
          }`}
        >
          {isUploading ? 'กำลังดำเนินการ...' : 'ชำระเงินและอัพโหลด 30฿'}
        </button>
      </form>
      {message && (
        <div className={`mt-4 p-3 rounded-md ${
          message.includes('ข้อผิดพลาด') ? 'bg-red-50 text-red-700' : 'bg-blue-50 text-blue-700'
        }`}>
          {message}
        </div>
      )}
    </div>
  );
};

// Video Feed Component
const VideoFeed = () => {
  const [videos, setVideos] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchVideos();
  }, []);

  const fetchVideos = async () => {
    try {
      const response = await axios.get(`${API}/videos`);
      setVideos(response.data.videos);
    } catch (error) {
      console.error('Error fetching videos:', error);
    } finally {
      setLoading(false);
    }
  };

  const recordView = async (videoId) => {
    try {
      await axios.post(`${API}/video/${videoId}/view`, {
        video_id: videoId,
        viewer_id: 'anonymous'
      });
    } catch (error) {
      console.error('Error recording view:', error);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {videos.map((video) => (
        <div key={video.id} className="bg-white rounded-lg shadow-md overflow-hidden">
          <div className="relative bg-gray-200 aspect-video">
            <video
              className="w-full h-full object-cover"
              controls
              onPlay={() => recordView(video.id)}
              poster="/api/placeholder/400/225"
            >
              <source src={`${API}/video/${video.id}/stream`} type="video/mp4" />
              เบราว์เซอร์ไม่รองรับการเล่นวิดีโอ
            </video>
          </div>
          <div className="p-4">
            <h3 className="font-semibold text-lg mb-2">{video.title}</h3>
            {video.description && (
              <p className="text-gray-600 text-sm mb-3">{video.description}</p>
            )}
            <div className="flex justify-between items-center text-sm text-gray-500">
              <span>👀 {video.view_count} ครั้ง</span>
              <span>{new Date(video.upload_date).toLocaleDateString('th-TH')}</span>
            </div>
          </div>
        </div>
      ))}
      {videos.length === 0 && (
        <div className="col-span-full text-center py-12">
          <p className="text-gray-500 text-lg">ยังไม่มีวิดีโอในรอบนี้</p>
        </div>
      )}
    </div>
  );
};

// Leaderboard Component
const Leaderboard = () => {
  const [leaderboard, setLeaderboard] = useState([]);
  const [competitionInfo, setCompetitionInfo] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchLeaderboard();
  }, []);

  const fetchLeaderboard = async () => {
    try {
      const response = await axios.get(`${API}/leaderboard`);
      setLeaderboard(response.data.leaderboard.slice(0, 20)); // Show top 20
      setCompetitionInfo(response.data.competition_info);
    } catch (error) {
      console.error('Error fetching leaderboard:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
      </div>
    );
  }

  const getTimeRemaining = () => {
    if (!competitionInfo?.end_date) return 'ไม่ทราบ';
    
    const endDate = new Date(competitionInfo.end_date);
    const now = new Date();
    const diff = endDate - now;
    
    if (diff <= 0) return 'จบแล้ว';
    
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
    const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    
    return `${days} วัน ${hours} ชั่วโมง`;
  };

  return (
    <div className="bg-white rounded-lg shadow-md">
      <div className="bg-gradient-to-r from-purple-600 to-pink-600 text-white p-6 rounded-t-lg">
        <h2 className="text-2xl font-bold mb-4">🏆 ลีดเดอร์บอร์ด</h2>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <p>💰 เงินรางวัลรวม</p>
            <p className="text-lg font-bold">{competitionInfo?.total_prize_pool?.toLocaleString() || 0} ฿</p>
          </div>
          <div>
            <p>⏰ เวลาที่เหลือ</p>
            <p className="text-lg font-bold">{getTimeRemaining()}</p>
          </div>
        </div>
      </div>
      
      <div className="p-6">
        <div className="space-y-3">
          {leaderboard.map((video, index) => (
            <div
              key={video.id}
              className={`flex items-center p-4 rounded-lg ${
                index < 3
                  ? 'bg-gradient-to-r from-yellow-50 to-orange-50 border-2 border-yellow-200'
                  : index < 10
                  ? 'bg-blue-50 border border-blue-200'
                  : 'bg-gray-50 border border-gray-200'
              }`}
            >
              <div className={`text-2xl font-bold mr-4 ${
                index === 0 ? 'text-yellow-500' :
                index === 1 ? 'text-gray-400' :
                index === 2 ? 'text-amber-600' : 'text-gray-600'
              }`}>
                #{index + 1}
              </div>
              <div className="flex-1">
                <h3 className="font-semibold">{video.title}</h3>
                <p className="text-sm text-gray-600">
                  👀 {video.view_count} ครั้ง | 
                  📅 {new Date(video.upload_date).toLocaleDateString('th-TH')}
                </p>
              </div>
              {index < 10 && (
                <div className="text-right">
                  <div className={`px-3 py-1 rounded-full text-xs font-medium ${
                    index === 0 ? 'bg-yellow-100 text-yellow-800' :
                    index < 3 ? 'bg-orange-100 text-orange-800' :
                    'bg-blue-100 text-blue-800'
                  }`}>
                    {index === 0 ? '🥇 TOP 1' :
                     index === 1 ? '🥈 TOP 2' :
                     index === 2 ? '🥉 TOP 3' : `TOP ${index + 1}`}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
        
        {leaderboard.length === 0 && (
          <div className="text-center py-8">
            <p className="text-gray-500">ยังไม่มีวิดีโอในการแข่งขัน</p>
          </div>
        )}
      </div>
    </div>
  );
};

// Payment Success Component
const PaymentSuccess = () => {
  const [sessionId, setSessionId] = useState('');
  const [videoId, setVideoId] = useState('');
  const [paymentStatus, setPaymentStatus] = useState('checking');
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState('');

  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const session = urlParams.get('session_id');
    const video = urlParams.get('video_id');
    
    if (session) {
      setSessionId(session);
      setVideoId(video);
      checkPaymentStatus(session);
    }
  }, []);

  const checkPaymentStatus = async (session) => {
    try {
      const response = await axios.get(`${API}/payment/status/${session}`);
      if (response.data.payment_status === 'paid') {
        setPaymentStatus('paid');
      } else {
        setTimeout(() => checkPaymentStatus(session), 2000);
      }
    } catch (error) {
      setPaymentStatus('error');
    }
  };

  const handleFileUpload = async (e) => {
    e.preventDefault();
    if (!selectedFile) {
      setMessage('กรุณาเลือกไฟล์วิดีโอ');
      return;
    }

    // Validate video duration (3 minutes max)
    if (selectedFile.size > 100 * 1024 * 1024) { // 100MB limit
      setMessage('ไฟล์ใหญ่เกินไป (สูงสุด 100MB)');
      return;
    }

    setUploading(true);
    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      await axios.post(`${API}/upload/video/${videoId}`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        }
      });
      
      setMessage('อัพโหลดสำเร็จ! วิดีโอของคุณเข้าสู่การแข่งขันแล้ว 🎉');
      setTimeout(() => {
        window.location.href = '/';
      }, 3000);
      
    } catch (error) {
      setMessage('เกิดข้อผิดพลาดในการอัพโหลด: ' + error.response?.data?.detail);
    } finally {
      setUploading(false);
    }
  };

  if (paymentStatus === 'checking') {
    return (
      <div className="max-w-md mx-auto bg-white rounded-xl shadow-md p-6 text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600 mx-auto mb-4"></div>
        <h2 className="text-xl font-bold mb-2">ตรวจสอบการชำระเงิน...</h2>
        <p className="text-gray-600">กรุณารอสักครู่</p>
      </div>
    );
  }

  if (paymentStatus === 'error') {
    return (
      <div className="max-w-md mx-auto bg-white rounded-xl shadow-md p-6 text-center">
        <h2 className="text-xl font-bold mb-2 text-red-600">เกิดข้อผิดพลาด</h2>
        <p className="text-gray-600 mb-4">ไม่สามารถตรวจสอบการชำระเงินได้</p>
        <button
          onClick={() => window.location.href = '/'}
          className="bg-purple-600 text-white px-4 py-2 rounded-md hover:bg-purple-700"
        >
          กลับหน้าหลัก
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-md mx-auto bg-white rounded-xl shadow-md p-6">
      <div className="text-center mb-6">
        <div className="text-green-500 text-4xl mb-2">✅</div>
        <h2 className="text-xl font-bold text-green-600">ชำระเงินสำเร็จ!</h2>
        <p className="text-gray-600">ตอนนี้คุณสามารถอัพโหลดวิดีโอได้แล้ว</p>
      </div>

      <form onSubmit={handleFileUpload}>
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            เลือกไฟล์วิดีโอ (สูงสุด 3 นาที)
          </label>
          <input
            type="file"
            accept="video/*"
            onChange={(e) => setSelectedFile(e.target.files[0])}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
          />
        </div>

        <button
          type="submit"
          disabled={uploading || !selectedFile}
          className={`w-full py-3 px-4 rounded-md font-medium ${
            uploading || !selectedFile
              ? 'bg-gray-400 cursor-not-allowed'
              : 'bg-purple-600 hover:bg-purple-700 text-white'
          }`}
        >
          {uploading ? 'กำลังอัพโหลด...' : 'อัพโหลดวิดีโอ'}
        </button>
      </form>

      {message && (
        <div className={`mt-4 p-3 rounded-md ${
          message.includes('ข้อผิดพลาด') ? 'bg-red-50 text-red-700' : 'bg-green-50 text-green-700'
        }`}>
          {message}
        </div>
      )}
    </div>
  );
};

// Main App Component
const App = () => {
  const [currentView, setCurrentView] = useState('home');

  // Check if returning from payment
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('session_id')) {
      setCurrentView('payment-success');
    }
  }, []);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-gradient-to-r from-purple-600 to-pink-600 text-white shadow-lg">
        <div className="container mx-auto px-4 py-6">
          <h1 className="text-4xl font-bold text-center mb-2">
            🎬 Pego
          </h1>
          <p className="text-center text-purple-100">
            แพลตฟอร์มแข่งขันวิดีโอสั้น • ลงคลิป 30฿ • รางวัลรวม 70%
          </p>
        </div>
      </header>

      {/* Hero Section */}
      <section className="bg-white py-12">
        <div className="container mx-auto px-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div>
              <h2 className="text-4xl font-bold text-gray-800 mb-6">
                สร้างสรรค์ แชร์ แข่งขัน
              </h2>
              <div className="space-y-4 text-lg text-gray-600 mb-8">
                <div className="flex items-center">
                  <span className="text-2xl mr-3">🎥</span>
                  <span>อัพโหลดวิดีโอสั้นสูงสุด 3 นาที</span>
                </div>
                <div className="flex items-center">
                  <span className="text-2xl mr-3">💰</span>
                  <span>เพียง 30 บาทต่อคลิป</span>
                </div>
                <div className="flex items-center">
                  <span className="text-2xl mr-3">🏆</span>
                  <span>วิดีโอ Top 1,000 รับรางวัล 70% ของรายได้</span>
                </div>
                <div className="flex items-center">
                  <span className="text-2xl mr-3">⏰</span>
                  <span>แข่งขันทุกรอบ 7 วัน</span>
                </div>
              </div>
            </div>
            <div className="flex justify-center">
              <img
                src="https://images.unsplash.com/photo-1686399237674-2de90fb2d25e"
                alt="Video Creation"
                className="rounded-lg shadow-lg max-w-full h-auto"
                style={{ maxHeight: '400px' }}
              />
            </div>
          </div>
        </div>
      </section>

      {/* Navigation */}
      {currentView !== 'payment-success' && (
        <nav className="bg-white shadow-md sticky top-0 z-10">
          <div className="container mx-auto px-4">
            <div className="flex justify-center space-x-8 py-4">
              <button
                onClick={() => setCurrentView('home')}
                className={`px-6 py-2 font-medium rounded-full ${
                  currentView === 'home'
                    ? 'bg-purple-600 text-white'
                    : 'text-gray-600 hover:text-purple-600'
                }`}
              >
                🏠 หน้าหลัก
              </button>
              <button
                onClick={() => setCurrentView('upload')}
                className={`px-6 py-2 font-medium rounded-full ${
                  currentView === 'upload'
                    ? 'bg-purple-600 text-white'
                    : 'text-gray-600 hover:text-purple-600'
                }`}
              >
                📤 อัพโหลด
              </button>
              <button
                onClick={() => setCurrentView('leaderboard')}
                className={`px-6 py-2 font-medium rounded-full ${
                  currentView === 'leaderboard'
                    ? 'bg-purple-600 text-white'
                    : 'text-gray-600 hover:text-purple-600'
                }`}
              >
                🏆 ลีดเดอร์บอร์ด
              </button>
            </div>
          </div>
        </nav>
      )}

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        {currentView === 'home' && <VideoFeed />}
        {currentView === 'upload' && <VideoUpload />}
        {currentView === 'leaderboard' && <Leaderboard />}
        {currentView === 'payment-success' && <PaymentSuccess />}
      </main>

      {/* Footer */}
      <footer className="bg-gray-800 text-white py-8 mt-16">
        <div className="container mx-auto px-4 text-center">
          <h3 className="text-xl font-bold mb-4">🎬 Pego</h3>
          <p className="text-gray-300 mb-4">
            แพลตฟอร์มแข่งขันวิดีโอสั้นที่ใหญ่ที่สุดในไทย
          </p>
          <div className="flex justify-center space-x-6 text-sm text-gray-400">
            <span>📧 support@pego.com</span>
            <span>📞 02-xxx-xxxx</span>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default App;