import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import axios from 'axios';

const SearchPage = () => {
  const { user, isAuthenticated } = useAuth();
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState({
    users: [],
    videos: [],
    hashtags: []
  });
  const [activeTab, setActiveTab] = useState('all'); // 'all', 'users', 'videos', 'hashtags'
  const [loading, setLoading] = useState(false);
  const [recentSearches, setRecentSearches] = useState([]);

  const API_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001/api';

  // Mock trending data
  const trendingData = {
    hashtags: [
      { tag: '#ทำอาหาร', count: '2.1M', icon: '🍳' },
      { tag: '#เต้น', count: '1.8M', icon: '💃' },
      { tag: '#รีวิว', count: '1.2M', icon: '📱' },
      { tag: '#ตลก', count: '987K', icon: '😂' },
      { tag: '#แต่งหน้า', count: '756K', icon: '💄' },
      { tag: '#ออกกำลังกาย', count: '623K', icon: '💪' },
      { tag: '#เพลง', count: '534K', icon: '🎵' },
      { tag: '#สัตว์เลี้ยง', count: '445K', icon: '🐕' }
    ],
    users: [
      { 
        id: 1, 
        username: 'chef_nong', 
        display_name: 'เชฟหนง', 
        avatar: '👨‍🍳', 
        followers: 125000, 
        verified: true,
        bio: 'สอนทำอาหารไทยแท้ 🍜'
      },
      { 
        id: 2, 
        username: 'dance_queen', 
        display_name: 'ราชินีเต้น', 
        avatar: '💃', 
        followers: 89000, 
        verified: false,
        bio: 'เต้นเพลงฮิตทุกวัน 💃'
      },
      { 
        id: 3, 
        username: 'tech_reviewer', 
        display_name: 'เทครีวิว', 
        avatar: '📱', 
        followers: 234000, 
        verified: true,
        bio: 'รีวิวแกดเจ็ตล่าสุด 📱'
      }
    ]
  };

  useEffect(() => {
    // Load recent searches from localStorage
    const saved = localStorage.getItem('pego_recent_searches');
    if (saved) {
      setRecentSearches(JSON.parse(saved));
    }
  }, []);

  const handleSearch = async (query) => {
    if (!query.trim()) {
      setSearchResults({ users: [], videos: [], hashtags: [] });
      return;
    }

    setLoading(true);
    
    try {
      // Mock search results - replace with actual API calls
      const mockResults = {
        users: trendingData.users.filter(user => 
          user.username.toLowerCase().includes(query.toLowerCase()) ||
          user.display_name.toLowerCase().includes(query.toLowerCase())
        ),
        videos: [
          {
            id: 1,
            title: `วิดีโอเกี่ยวกับ ${query}`,
            thumbnail: '🎬',
            user: trendingData.users[0],
            views: 12500,
            likes: 890,
            duration: '1:23'
          },
          {
            id: 2,
            title: `สอน ${query} แบบง่ายๆ`,
            thumbnail: '📚',
            user: trendingData.users[1],
            views: 3400,
            likes: 234,
            duration: '2:15'
          }
        ],
        hashtags: trendingData.hashtags.filter(hashtag =>
          hashtag.tag.toLowerCase().includes(query.toLowerCase())
        )
      };

      setSearchResults(mockResults);

      // Add to recent searches
      const newRecentSearches = [query, ...recentSearches.filter(s => s !== query)].slice(0, 5);
      setRecentSearches(newRecentSearches);
      localStorage.setItem('pego_recent_searches', JSON.stringify(newRecentSearches));

    } catch (error) {
      console.error('Search failed:', error);
    } finally {
      setLoading(false);
    }
  };

  const clearRecentSearches = () => {
    setRecentSearches([]);
    localStorage.removeItem('pego_recent_searches');
  };

  const formatNumber = (num) => {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
    return num.toString();
  };

  const renderSearchResults = () => {
    const hasResults = searchResults.users.length > 0 || searchResults.videos.length > 0 || searchResults.hashtags.length > 0;

    if (loading) {
      return (
        <div className="flex items-center justify-center py-12">
          <div className="text-center">
            <div className="text-4xl mb-2">🔍</div>
            <p className="text-gray-400">กำลังค้นหา...</p>
          </div>
        </div>
      );
    }

    if (!hasResults && searchQuery) {
      return (
        <div className="flex items-center justify-center py-12">
          <div className="text-center">
            <div className="text-6xl mb-4">😔</div>
            <h3 className="text-xl font-bold mb-2">ไม่พบผลการค้นหา</h3>
            <p className="text-gray-400">ลองค้นหาด้วยคำอื่น</p>
          </div>
        </div>
      );
    }

    // Show results based on active tab
    if (activeTab === 'users' || (activeTab === 'all' && searchResults.users.length > 0)) {
      return (
        <div className="space-y-4">
          {activeTab === 'all' && <h3 className="font-bold text-lg px-4">👥 ผู้ใช้</h3>}
          {searchResults.users.map((user) => (
            <div key={user.id} className="flex items-center justify-between px-4 py-3 bg-gray-900 mx-4 rounded-lg">
              <div className="flex items-center space-x-3">
                <div className="w-12 h-12 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full flex items-center justify-center text-white font-bold">
                  {user.avatar}
                </div>
                <div>
                  <div className="flex items-center space-x-1">
                    <span className="font-bold text-white">{user.display_name}</span>
                    {user.verified && <span className="text-blue-400">✓</span>}
                  </div>
                  <p className="text-sm text-gray-400">@{user.username}</p>
                  <p className="text-xs text-gray-500">{formatNumber(user.followers)} ผู้ติดตาม</p>
                </div>
              </div>
              <button className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 px-4 py-2 rounded-lg font-medium transition-all">
                ติดตาม
              </button>
            </div>
          ))}
        </div>
      );
    }

    if (activeTab === 'videos' || (activeTab === 'all' && searchResults.videos.length > 0)) {
      return (
        <div className="space-y-4">
          {activeTab === 'all' && <h3 className="font-bold text-lg px-4">🎬 วิดีโอ</h3>}
          <div className="grid grid-cols-2 gap-2 px-4">
            {searchResults.videos.map((video) => (
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
        </div>
      );
    }

    if (activeTab === 'hashtags' || (activeTab === 'all' && searchResults.hashtags.length > 0)) {
      return (
        <div className="space-y-4">
          {activeTab === 'all' && <h3 className="font-bold text-lg px-4"># แฮชแท็ก</h3>}
          {searchResults.hashtags.map((hashtag, index) => (
            <div key={index} className="flex items-center justify-between px-4 py-3 bg-gray-900 mx-4 rounded-lg">
              <div className="flex items-center space-x-3">
                <div className="text-2xl">{hashtag.icon}</div>
                <div>
                  <p className="font-bold text-white">{hashtag.tag}</p>
                  <p className="text-sm text-gray-400">{hashtag.count} โพสต์</p>
                </div>
              </div>
              <button className="text-gray-400 hover:text-white transition-all">
                →
              </button>
            </div>
          ))}
        </div>
      );
    }

    return null;
  };

  return (
    <div className="min-h-screen bg-black text-white">
      {/* Search Header */}
      <div className="sticky top-0 bg-black border-b border-gray-800 z-10">
        <div className="p-4">
          {/* Search Input */}
          <div className="relative">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value);
                handleSearch(e.target.value);
              }}
              placeholder="ค้นหา ผู้ใช้, วิดีโอ, แฮชแท็ก..."
              className="w-full bg-gray-800 border border-gray-600 rounded-full px-4 py-3 pl-12 text-white placeholder-gray-400 focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            />
            <div className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400 text-xl">
              🔍
            </div>
            {searchQuery && (
              <button
                onClick={() => {
                  setSearchQuery('');
                  setSearchResults({ users: [], videos: [], hashtags: [] });
                }}
                className="absolute right-4 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-white"
              >
                ✕
              </button>
            )}
          </div>

          {/* Search Tabs */}
          {searchQuery && (
            <div className="flex space-x-1 mt-4 bg-gray-900 rounded-lg p-1">
              {[
                { id: 'all', label: 'ทั้งหมด' },
                { id: 'users', label: 'ผู้ใช้' },
                { id: 'videos', label: 'วิดีโอ' },
                { id: 'hashtags', label: 'แฮชแท็ก' }
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex-1 py-2 px-3 rounded-md font-medium transition-all ${
                    activeTab === tab.id
                      ? 'bg-white text-black'
                      : 'text-gray-400 hover:text-white'
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Content */}
      <div className="pb-6">
        {searchQuery ? (
          renderSearchResults()
        ) : (
          <div className="space-y-6">
            {/* Recent Searches */}
            {recentSearches.length > 0 && (
              <div className="px-4">
                <div className="flex justify-between items-center mb-4">
                  <h3 className="font-bold text-lg">🕐 ค้นหาล่าสุด</h3>
                  <button
                    onClick={clearRecentSearches}
                    className="text-gray-400 hover:text-white text-sm transition-all"
                  >
                    ล้างทั้งหมด
                  </button>
                </div>
                <div className="space-y-2">
                  {recentSearches.map((search, index) => (
                    <button
                      key={index}
                      onClick={() => {
                        setSearchQuery(search);
                        handleSearch(search);
                      }}
                      className="flex items-center justify-between w-full p-3 bg-gray-900 rounded-lg hover:bg-gray-800 transition-all"
                    >
                      <span className="text-white">{search}</span>
                      <span className="text-gray-400">↗️</span>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Trending Hashtags */}
            <div className="px-4">
              <h3 className="font-bold text-lg mb-4">🔥 แฮชแท็กยอดนิยม</h3>
              <div className="space-y-2">
                {trendingData.hashtags.slice(0, 6).map((hashtag, index) => (
                  <button
                    key={index}
                    onClick={() => {
                      setSearchQuery(hashtag.tag);
                      handleSearch(hashtag.tag);
                    }}
                    className="flex items-center justify-between w-full p-3 bg-gray-900 rounded-lg hover:bg-gray-800 transition-all"
                  >
                    <div className="flex items-center space-x-3">
                      <span className="text-xl">{hashtag.icon}</span>
                      <div className="text-left">
                        <p className="font-bold text-white">{hashtag.tag}</p>
                        <p className="text-sm text-gray-400">{hashtag.count} โพสต์</p>
                      </div>
                    </div>
                    <span className="text-gray-400">→</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Suggested Users */}
            <div className="px-4">
              <h3 className="font-bold text-lg mb-4">👥 ผู้ใช้แนะนำ</h3>
              <div className="space-y-3">
                {trendingData.users.map((user) => (
                  <div key={user.id} className="flex items-center justify-between p-3 bg-gray-900 rounded-lg">
                    <div className="flex items-center space-x-3">
                      <div className="w-12 h-12 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full flex items-center justify-center text-white font-bold">
                        {user.avatar}
                      </div>
                      <div>
                        <div className="flex items-center space-x-1">
                          <span className="font-bold text-white">{user.display_name}</span>
                          {user.verified && <span className="text-blue-400">✓</span>}
                        </div>
                        <p className="text-sm text-gray-400">@{user.username}</p>
                        <p className="text-xs text-gray-500">{user.bio}</p>
                      </div>
                    </div>
                    <button className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 px-4 py-2 rounded-lg font-medium transition-all">
                      ติดตาม
                    </button>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default SearchPage;