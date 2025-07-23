import React, { useState, useEffect } from 'react';
import { useAdminAuth } from '../contexts/AdminAuthContext';

const AdminDashboard = () => {
  const { admin, logout, apiCall } = useAdminAuth();
  const [activeTab, setActiveTab] = useState('overview');
  const [stats, setStats] = useState(null);
  const [users, setUsers] = useState([]);
  const [videos, setVideos] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      const [dashboardStats, usersData, videosData] = await Promise.all([
        apiCall('/dashboard'),
        apiCall('/users?limit=20'),
        apiCall('/videos?limit=20')
      ]);
      
      setStats(dashboardStats);
      setUsers(usersData.users || []);
      setVideos(videosData.videos || []);
    } catch (error) {
      console.error('Error loading dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleUserAction = async (userId, action, reason = '') => {
    try {
      await apiCall(`/users/${userId}/${action}`, {
        method: 'POST',
        body: JSON.stringify({ reason })
      });
      await loadDashboardData(); // Reload data
      alert(`ดำเนินการ ${action} สำเร็จ`);
    } catch (error) {
      alert(`เกิดข้อผิดพลาด: ${error.message}`);
    }
  };

  const handleVideoAction = async (videoId, action) => {
    try {
      if (action === 'delete') {
        if (!confirm('คุณแน่ใจหรือไม่ที่จะลบวิดีโอนี้?')) return;
        await apiCall(`/videos/${videoId}`, { method: 'DELETE' });
      } else {
        await apiCall('/videos/moderate', {
          method: 'POST',
          body: JSON.stringify({
            video_ids: [videoId],
            action: action
          })
        });
      }
      await loadDashboardData(); // Reload data
      alert('ดำเนินการสำเร็จ');
    } catch (error) {
      alert(`เกิดข้อผิดพลาด: ${error.message}`);
    }
  };

  const formatDate = (dateString) => {
    return new Intl.DateTimeFormat('th-TH', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    }).format(new Date(dateString));
  };

  const formatNumber = (num) => {
    return new Intl.NumberFormat('th-TH').format(num);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-white text-xl">กำลังโหลด...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900">
      {/* Header */}
      <header className="bg-gray-800 shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center">
              <h1 className="text-3xl font-bold text-white">Pego Admin</h1>
              <span className="ml-4 px-3 py-1 bg-blue-600 text-white text-sm rounded-full">
                {admin?.role}
              </span>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-gray-300">สวัสดี, {admin?.username}</span>
              <button
                onClick={logout}
                className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-md text-sm"
              >
                ออกจากระบบ
              </button>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Navigation Tabs */}
        <div className="border-b border-gray-700 mb-8">
          <nav className="-mb-px flex space-x-8">
            {[
              { id: 'overview', name: 'ภาพรวม', icon: '📊' },
              { id: 'users', name: 'จัดการผู้ใช้', icon: '👥' },
              { id: 'videos', name: 'จัดการวิดีโอ', icon: '🎬' },
              { id: 'financial', name: 'การเงิน', icon: '💰' },
              { id: 'settings', name: 'ตั้งค่า', icon: '⚙️' }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-400'
                    : 'border-transparent text-gray-400 hover:text-gray-300 hover:border-gray-300'
                } whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm flex items-center space-x-2`}
              >
                <span>{tab.icon}</span>
                <span>{tab.name}</span>
              </button>
            ))}
          </nav>
        </div>

        {/* Overview Tab */}
        {activeTab === 'overview' && stats && (
          <div className="space-y-6">
            {/* Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <div className="bg-gray-800 rounded-lg p-6">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <div className="text-2xl">👥</div>
                  </div>
                  <div className="ml-4">
                    <div className="text-sm font-medium text-gray-400">ผู้ใช้ทั้งหมด</div>
                    <div className="text-2xl font-bold text-white">
                      {formatNumber(stats.overview?.total_users || 0)}
                    </div>
                  </div>
                </div>
              </div>
              
              <div className="bg-gray-800 rounded-lg p-6">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <div className="text-2xl">🎬</div>
                  </div>
                  <div className="ml-4">
                    <div className="text-sm font-medium text-gray-400">วิดีโอทั้งหมด</div>
                    <div className="text-2xl font-bold text-white">
                      {formatNumber(stats.overview?.total_videos || 0)}
                    </div>
                  </div>
                </div>
              </div>
              
              <div className="bg-gray-800 rounded-lg p-6">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <div className="text-2xl">💰</div>
                  </div>
                  <div className="ml-4">
                    <div className="text-sm font-medium text-gray-400">รายได้วันนี้</div>
                    <div className="text-2xl font-bold text-white">
                      ฿{formatNumber(stats.today?.total_revenue || 0)}
                    </div>
                  </div>
                </div>
              </div>
              
              <div className="bg-gray-800 rounded-lg p-6">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <div className="text-2xl">✨</div>
                  </div>
                  <div className="ml-4">
                    <div className="text-sm font-medium text-gray-400">ผู้ใช้ใหม่วันนี้</div>
                    <div className="text-2xl font-bold text-white">
                      {formatNumber(stats.today?.new_users || 0)}
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Current Competition */}
            {stats.current_competition && (
              <div className="bg-gray-800 rounded-lg p-6">
                <h3 className="text-lg font-medium text-white mb-4">การแข่งขันปัจจุบัน</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <div className="text-sm text-gray-400">ชื่อการแข่งขัน</div>
                    <div className="text-white font-medium">{stats.current_competition.title}</div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-400">จำนวนผู้เข้าร่วม</div>
                    <div className="text-white font-medium">{formatNumber(stats.current_competition.participant_count)}</div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-400">เงินรางวัล</div>
                    <div className="text-white font-medium">฿{formatNumber(stats.current_competition.prize_pool)}</div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Users Tab */}
        {activeTab === 'users' && (
          <div className="space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-2xl font-bold text-white">จัดการผู้ใช้</h2>
              <button
                onClick={loadDashboardData}
                className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md"
              >
                รีเฟรช
              </button>
            </div>
            
            <div className="bg-gray-800 rounded-lg overflow-hidden">
              <table className="min-w-full divide-y divide-gray-700">
                <thead className="bg-gray-700">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                      ผู้ใช้
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                      สถานะ
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                      วิดีโอ
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                      เครดิต
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                      การดำเนินการ
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-gray-800 divide-y divide-gray-700">
                  {users.map((user) => (
                    <tr key={user.id}>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <div className="flex-shrink-0 h-10 w-10">
                            <div className="h-10 w-10 rounded-full bg-blue-600 flex items-center justify-center">
                              <span className="text-white font-medium">
                                {user.display_name?.charAt(0) || user.username?.charAt(0)}
                              </span>
                            </div>
                          </div>
                          <div className="ml-4">
                            <div className="text-sm font-medium text-white">
                              {user.display_name || user.username}
                              {user.is_verified && <span className="ml-1 text-blue-400">✓</span>}
                            </div>
                            <div className="text-sm text-gray-400">@{user.username}</div>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                          user.is_active 
                            ? 'bg-green-900 text-green-200' 
                            : 'bg-red-900 text-red-200'
                        }`}>
                          {user.is_active ? 'ใช้งานได้' : 'ถูกแบน'}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                        {user.video_count || 0}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                        {formatNumber(user.credits || 0)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
                        {user.is_active ? (
                          <button
                            onClick={() => handleUserAction(user.id, 'ban', prompt('เหตุผลในการแบน:'))}
                            className="text-red-400 hover:text-red-300"
                          >
                            แบน
                          </button>
                        ) : (
                          <button
                            onClick={() => handleUserAction(user.id, 'unban')}
                            className="text-green-400 hover:text-green-300"
                          >
                            ปลดแบน
                          </button>
                        )}
                        <button
                          onClick={() => {
                            const amount = prompt('ปรับเครดิต (ใส่ - สำหรับลด):');
                            const reason = prompt('เหตุผล:');
                            if (amount && reason) {
                              apiCall(`/users/${user.id}/credits/adjust`, {
                                method: 'POST',
                                body: JSON.stringify({ amount: parseInt(amount), reason })
                              }).then(() => {
                                alert('ปรับเครดิตสำเร็จ');
                                loadDashboardData();
                              }).catch(err => alert(`เกิดข้อผิดพลาด: ${err.message}`));
                            }
                          }}
                          className="text-yellow-400 hover:text-yellow-300"
                        >
                          ปรับเครดิต
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Videos Tab */}
        {activeTab === 'videos' && (
          <div className="space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-2xl font-bold text-white">จัดการวิดีโอ</h2>
              <button
                onClick={loadDashboardData}
                className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md"
              >
                รีเฟรช
              </button>
            </div>
            
            <div className="bg-gray-800 rounded-lg overflow-hidden">
              <table className="min-w-full divide-y divide-gray-700">
                <thead className="bg-gray-700">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                      วิดีโอ
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                      ผู้สร้าง
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                      สถิติ
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                      สถานะ
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                      การดำเนินการ
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-gray-800 divide-y divide-gray-700">
                  {videos.map((video) => (
                    <tr key={video.id}>
                      <td className="px-6 py-4">
                        <div>
                          <div className="text-sm font-medium text-white">{video.title}</div>
                          <div className="text-sm text-gray-400">
                            {formatDate(video.upload_date)}
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-white">
                          {video.user?.display_name || 'Unknown'}
                          {video.user?.is_verified && <span className="ml-1 text-blue-400">✓</span>}
                        </div>
                        <div className="text-sm text-gray-400">@{video.user?.username}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                        <div>👁️ {formatNumber(video.view_count || 0)}</div>
                        <div>❤️ {formatNumber(video.like_count || 0)}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                          video.status === 'active' 
                            ? 'bg-green-900 text-green-200' 
                            : 'bg-red-900 text-red-200'
                        }`}>
                          {video.status === 'active' ? 'ใช้งานได้' : 'ถูกระงับ'}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
                        {video.status === 'active' ? (
                          <button
                            onClick={() => handleVideoAction(video.id, 'suspend')}
                            className="text-red-400 hover:text-red-300"
                          >
                            ระงับ
                          </button>
                        ) : (
                          <button
                            onClick={() => handleVideoAction(video.id, 'approve')}
                            className="text-green-400 hover:text-green-300"
                          >
                            อนุมัติ
                          </button>
                        )}
                        <button
                          onClick={() => handleVideoAction(video.id, 'delete')}
                          className="text-red-400 hover:text-red-300"
                        >
                          ลบ
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Financial Tab */}
        {activeTab === 'financial' && (
          <div className="space-y-6">
            <h2 className="text-2xl font-bold text-white">จัดการการเงิน</h2>
            
            <div className="bg-gray-800 rounded-lg p-6">
              <h3 className="text-lg font-medium text-white mb-4">ตั้งค่าราคา</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-300">ราคาอัปโหลดวิดีโอ (บาท)</label>
                  <input
                    type="number"
                    defaultValue="30"
                    className="mt-1 block w-full bg-gray-700 border border-gray-600 rounded-md px-3 py-2 text-white"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300">เปอร์เซ็นต์เงินรางวัล (%)</label>
                  <input
                    type="number"
                    defaultValue="70"
                    className="mt-1 block w-full bg-gray-700 border border-gray-600 rounded-md px-3 py-2 text-white"
                  />
                </div>
              </div>
              <button className="mt-4 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md">
                บันทึกการตั้งค่า
              </button>
            </div>
          </div>
        )}

        {/* Settings Tab */}
        {activeTab === 'settings' && (
          <div className="space-y-6">
            <h2 className="text-2xl font-bold text-white">ตั้งค่าระบบ</h2>
            
            <div className="bg-gray-800 rounded-lg p-6">
              <h3 className="text-lg font-medium text-white mb-4">ตั้งค่าทั่วไป</h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300">ระยะเวลาการแข่งขัน (วัน)</label>
                  <input
                    type="number"
                    defaultValue="7"
                    className="mt-1 block w-full bg-gray-700 border border-gray-600 rounded-md px-3 py-2 text-white"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300">ขนาดไฟล์วิดีโอสูงสุด (MB)</label>
                  <input
                    type="number"
                    defaultValue="100"
                    className="mt-1 block w-full bg-gray-700 border border-gray-600 rounded-md px-3 py-2 text-white"
                  />
                </div>
              </div>
              <button className="mt-4 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md">
                บันทึกการตั้งค่า
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AdminDashboard;