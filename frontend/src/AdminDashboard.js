import React, { useState, useEffect } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const ADMIN_API = `${BACKEND_URL}/api/admin`;

// Admin Login Component
const AdminLogin = ({ onLogin }) => {
  const [credentials, setCredentials] = useState({ username: '', password: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await axios.post(`${ADMIN_API}/login`, credentials);
      localStorage.setItem('admin_token', response.data.access_token);
      localStorage.setItem('admin_user', JSON.stringify(response.data.admin));
      onLogin(response.data.admin);
    } catch (error) {
      setError(error.response?.data?.detail || 'เกิดข้อผิดพลาดในการเข้าสู่ระบบ');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 flex items-center justify-center">
      <div className="bg-white p-8 rounded-lg shadow-xl w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-800">🎬 Pego Admin</h1>
          <p className="text-gray-600 mt-2">ระบบจัดการหลังบ้าน</p>
        </div>

        <form onSubmit={handleLogin} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              ชื่อผู้ใช้
            </label>
            <input
              type="text"
              value={credentials.username}
              onChange={(e) => setCredentials({ ...credentials, username: e.target.value })}
              className="w-full px-3 py-3 border border-gray-300 rounded-lg focus:outline-none focus:border-purple-500"
              placeholder="ใส่ชื่อผู้ใช้"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              รหัสผ่าน
            </label>
            <input
              type="password"
              value={credentials.password}
              onChange={(e) => setCredentials({ ...credentials, password: e.target.value })}
              className="w-full px-3 py-3 border border-gray-300 rounded-lg focus:outline-none focus:border-purple-500"
              placeholder="ใส่รหัสผ่าน"
              required
            />
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className={`w-full py-3 px-4 rounded-lg font-medium transition-colors ${
              loading
                ? 'bg-gray-400 cursor-not-allowed'
                : 'bg-purple-600 hover:bg-purple-700 text-white'
            }`}
          >
            {loading ? 'กำลังเข้าสู่ระบบ...' : 'เข้าสู่ระบบ'}
          </button>
        </form>
      </div>
    </div>
  );
};

// Dashboard Overview Component
const DashboardOverview = () => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      const token = localStorage.getItem('admin_token');
      const response = await axios.get(`${ADMIN_API}/dashboard`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setStats(response.data);
    } catch (error) {
      console.error('Error fetching stats:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Overview Cards */}
        <div className="bg-gradient-to-r from-purple-500 to-purple-600 text-white p-6 rounded-lg">
          <div className="flex items-center">
            <span className="text-3xl mr-3">👥</span>
            <div>
              <p className="text-purple-100">ผู้ใช้ทั้งหมด</p>
              <p className="text-2xl font-bold">{stats?.overview?.total_users?.toLocaleString() || 0}</p>
            </div>
          </div>
        </div>

        <div className="bg-gradient-to-r from-blue-500 to-blue-600 text-white p-6 rounded-lg">
          <div className="flex items-center">
            <span className="text-3xl mr-3">🎬</span>
            <div>
              <p className="text-blue-100">วิดีโอทั้งหมด</p>
              <p className="text-2xl font-bold">{stats?.overview?.total_videos?.toLocaleString() || 0}</p>
            </div>
          </div>
        </div>

        <div className="bg-gradient-to-r from-green-500 to-green-600 text-white p-6 rounded-lg">
          <div className="flex items-center">
            <span className="text-3xl mr-3">🏆</span>
            <div>
              <p className="text-green-100">การแข่งขันทั้งหมด</p>
              <p className="text-2xl font-bold">{stats?.overview?.total_competitions || 0}</p>
            </div>
          </div>
        </div>

        <div className="bg-gradient-to-r from-yellow-500 to-yellow-600 text-white p-6 rounded-lg">
          <div className="flex items-center">
            <span className="text-3xl mr-3">💰</span>
            <div>
              <p className="text-yellow-100">รายได้วันนี้</p>
              <p className="text-2xl font-bold">{stats?.today?.total_revenue?.toLocaleString() || 0} ฿</p>
            </div>
          </div>
        </div>
      </div>

      {/* Current Competition */}
      {stats?.current_competition && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-xl font-bold mb-4 flex items-center">
            🏆 การแข่งขันปัจจุบัน
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <h4 className="font-semibold text-lg">{stats.current_competition.title}</h4>
              <p className="text-gray-600">
                วันที่เหลือ: {stats.current_competition.days_remaining} วัน
              </p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-purple-600">
                {stats.current_competition.participant_count}
              </p>
              <p className="text-sm text-gray-600">ผู้เข้าร่วม</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-green-600">
                {stats.current_competition.prize_pool?.toLocaleString()} ฿
              </p>
              <p className="text-sm text-gray-600">เงินรางวัล</p>
            </div>
          </div>
        </div>
      )}

      {/* Today's Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center">
            <span className="text-2xl mr-3">👤</span>
            <div>
              <p className="text-gray-600">ผู้ใช้ใหม่วันนี้</p>
              <p className="text-xl font-bold">{stats?.today?.new_users || 0}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center">
            <span className="text-2xl mr-3">📹</span>
            <div>
              <p className="text-gray-600">วิดีโอใหม่วันนี้</p>
              <p className="text-xl font-bold">{stats?.today?.new_videos || 0}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center">
            <span className="text-2xl mr-3">👀</span>
            <div>
              <p className="text-gray-600">ยอดวิววันนี้</p>
              <p className="text-xl font-bold">{stats?.today?.total_views?.toLocaleString() || 0}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Competition Management Component
const CompetitionManagement = () => {
  const [competitions, setCompetitions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newCompetition, setNewCompetition] = useState({
    title: '',
    description: '',
    duration_days: 7,
    entry_fee: 30,
    winner_count: 1000,
    special_winner_count: 10
  });

  useEffect(() => {
    fetchCompetitions();
  }, []);

  const fetchCompetitions = async () => {
    try {
      const token = localStorage.getItem('admin_token');
      const response = await axios.get(`${ADMIN_API}/competitions`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setCompetitions(response.data.competitions);
    } catch (error) {
      console.error('Error fetching competitions:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateCompetition = async (e) => {
    e.preventDefault();
    try {
      const token = localStorage.getItem('admin_token');
      await axios.post(`${ADMIN_API}/competitions`, newCompetition, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      alert('สร้างการแข่งขันสำเร็จ!');
      setShowCreateForm(false);
      fetchCompetitions();
      setNewCompetition({
        title: '',
        description: '',
        duration_days: 7,
        entry_fee: 30,
        winner_count: 1000,
        special_winner_count: 10
      });
    } catch (error) {
      alert('เกิดข้อผิดพลาด: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleEndCompetition = async (competitionId) => {
    if (!confirm('คุณแน่ใจหรือไม่ที่จะจบการแข่งขันนี้?')) return;

    try {
      const token = localStorage.getItem('admin_token');
      await axios.put(`${ADMIN_API}/competitions/${competitionId}/end`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      alert('จบการแข่งขันสำเร็จ!');
      fetchCompetitions();
    } catch (error) {
      alert('เกิดข้อผิดพลาด: ' + (error.response?.data?.detail || error.message));
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold">จัดการการแข่งขัน</h2>
        <button
          onClick={() => setShowCreateForm(!showCreateForm)}
          className="bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 transition-colors"
        >
          + สร้างการแข่งขันใหม่
        </button>
      </div>

      {showCreateForm && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-bold mb-4">สร้างการแข่งขันใหม่</h3>
          <form onSubmit={handleCreateCompetition} className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">ชื่อการแข่งขัน *</label>
              <input
                type="text"
                value={newCompetition.title}
                onChange={(e) => setNewCompetition({ ...newCompetition, title: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-purple-500"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">ระยะเวลา (วัน)</label>
              <input
                type="number"
                value={newCompetition.duration_days}
                onChange={(e) => setNewCompetition({ ...newCompetition, duration_days: parseInt(e.target.value) })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-purple-500"
                min="1"
                max="30"
              />
            </div>

            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-1">คำอธิบาย</label>
              <textarea
                value={newCompetition.description}
                onChange={(e) => setNewCompetition({ ...newCompetition, description: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-purple-500"
                rows={3}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">ค่าเข้าร่วม (฿)</label>
              <input
                type="number"
                value={newCompetition.entry_fee}
                onChange={(e) => setNewCompetition({ ...newCompetition, entry_fee: parseFloat(e.target.value) })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-purple-500"
                min="1"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">จำนวนผู้ชนะ</label>
              <input
                type="number"
                value={newCompetition.winner_count}
                onChange={(e) => setNewCompetition({ ...newCompetition, winner_count: parseInt(e.target.value) })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-purple-500"
                min="10"
              />
            </div>

            <div className="md:col-span-2 flex space-x-4">
              <button
                type="submit"
                className="bg-purple-600 text-white px-6 py-2 rounded-lg hover:bg-purple-700 transition-colors"
              >
                สร้างการแข่งขัน
              </button>
              <button
                type="button"
                onClick={() => setShowCreateForm(false)}
                className="bg-gray-500 text-white px-6 py-2 rounded-lg hover:bg-gray-600 transition-colors"
              >
                ยกเลิก
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="grid grid-cols-1 gap-4">
        {competitions.map(competition => (
          <div key={competition.id} className="bg-white rounded-lg shadow-md p-6">
            <div className="flex justify-between items-start">
              <div className="flex-1">
                <div className="flex items-center space-x-3">
                  <h3 className="text-lg font-bold">{competition.title}</h3>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                    competition.status === 'active' 
                      ? 'bg-green-100 text-green-800'
                      : competition.status === 'ended'
                      ? 'bg-gray-100 text-gray-800'
                      : 'bg-blue-100 text-blue-800'
                  }`}>
                    {competition.status === 'active' ? 'กำลังแข่งขัน' :
                     competition.status === 'ended' ? 'จบแล้ว' : 'ร่าง'}
                  </span>
                </div>
                <p className="text-gray-600 mt-1">{competition.description}</p>
                
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
                  <div>
                    <p className="text-sm text-gray-600">ผู้เข้าร่วม</p>
                    <p className="font-bold">{competition.participant_count || 0}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">วิดีโอ</p>
                    <p className="font-bold">{competition.video_count || 0}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">เงินรางวัล</p>
                    <p className="font-bold">{(competition.prize_pool || 0).toLocaleString()} ฿</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">รายได้</p>
                    <p className="font-bold">{(competition.total_revenue || 0).toLocaleString()} ฿</p>
                  </div>
                </div>
                
                <div className="mt-3 text-sm text-gray-500">
                  <p>เริ่ม: {new Date(competition.start_date).toLocaleDateString('th-TH')}</p>
                  <p>สิ้นสุด: {new Date(competition.end_date).toLocaleDateString('th-TH')}</p>
                </div>
              </div>
              
              <div className="flex space-x-2">
                {competition.status === 'active' && (
                  <button
                    onClick={() => handleEndCompetition(competition.id)}
                    className="bg-red-500 text-white px-3 py-1 rounded text-sm hover:bg-red-600 transition-colors"
                  >
                    จบการแข่งขัน
                  </button>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

// Main Admin Dashboard Component
const AdminDashboard = () => {
  const [currentTab, setCurrentTab] = useState('dashboard');
  const [adminUser, setAdminUser] = useState(null);

  useEffect(() => {
    const token = localStorage.getItem('admin_token');
    const user = localStorage.getItem('admin_user');
    if (token && user) {
      setAdminUser(JSON.parse(user));
    }
  }, []);

  const handleLogin = (user) => {
    setAdminUser(user);
  };

  const handleLogout = () => {
    localStorage.removeItem('admin_token');
    localStorage.removeItem('admin_user');
    setAdminUser(null);
  };

  if (!adminUser) {
    return <AdminLogin onLogin={handleLogin} />;
  }

  const tabs = [
    { id: 'dashboard', name: 'แดชบอร์ด', icon: '📊' },
    { id: 'competitions', name: 'การแข่งขัน', icon: '🏆' },
    { id: 'videos', name: 'วิดีโอ', icon: '🎬' },
    { id: 'users', name: 'ผู้ใช้', icon: '👥' },
    { id: 'algorithm', name: 'อัลกอริทึม', icon: '🤖' },
    { id: 'analytics', name: 'วิเคราะห์', icon: '📈' }
  ];

  const renderContent = () => {
    switch (currentTab) {
      case 'dashboard':
        return <DashboardOverview />;
      case 'competitions':
        return <CompetitionManagement />;
      case 'videos':
        return <div className="text-center py-12"><p>ฟีเจอร์จัดการวิดีโอกำลังพัฒนา</p></div>;
      case 'users':
        return <div className="text-center py-12"><p>ฟีเจอร์จัดการผู้ใช้กำลังพัฒนา</p></div>;
      case 'algorithm':
        return <div className="text-center py-12"><p>ฟีเจอร์จัดการอัลกอริทึมกำลังพัฒนา</p></div>;
      case 'analytics':
        return <div className="text-center py-12"><p>ฟีเจอร์วิเคราะห์กำลังพัฒนา</p></div>;
      default:
        return <DashboardOverview />;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex">
      {/* Sidebar */}
      <div className="w-64 bg-white shadow-lg">
        <div className="p-6 border-b">
          <h1 className="text-xl font-bold text-gray-800">🎬 Pego Admin</h1>
          <p className="text-sm text-gray-600 mt-1">สวัสดี, {adminUser.username}</p>
        </div>
        
        <nav className="mt-6">
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => setCurrentTab(tab.id)}
              className={`w-full flex items-center px-6 py-3 text-left hover:bg-purple-50 transition-colors ${
                currentTab === tab.id ? 'bg-purple-100 border-r-2 border-purple-600' : ''
              }`}
            >
              <span className="text-xl mr-3">{tab.icon}</span>
              <span className={`font-medium ${currentTab === tab.id ? 'text-purple-700' : 'text-gray-700'}`}>
                {tab.name}
              </span>
            </button>
          ))}
        </nav>

        <div className="absolute bottom-0 w-64 p-6 border-t">
          <button
            onClick={handleLogout}
            className="w-full bg-gray-500 text-white py-2 px-4 rounded-lg hover:bg-gray-600 transition-colors"
          >
            ออกจากระบบ
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-x-hidden">
        <div className="p-8">
          {renderContent()}
        </div>
      </div>
    </div>
  );
};

export default AdminDashboard;