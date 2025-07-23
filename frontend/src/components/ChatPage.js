import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../contexts/AuthContext';
import axios from 'axios';

const ChatPage = () => {
  const { user, isAuthenticated } = useAuth();
  const [chatRooms, setChatRooms] = useState([]);
  const [selectedChat, setSelectedChat] = useState(null);
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const API_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001/api';

  // Mock chat data
  const mockChatRooms = [
    {
      id: 1,
      participants: ['current_user', 'chef_nong'],
      otherUser: {
        id: 'chef_nong',
        username: 'chef_nong',
        display_name: 'เชฟหนง',
        avatar: '👨‍🍳',
        online: true
      },
      lastMessage: 'สูตรผัดไทยอร่อยมาก!',
      lastMessageTime: '10:30',
      unreadCount: 2,
      updated_at: new Date()
    },
    {
      id: 2,
      participants: ['current_user', 'dance_queen'],
      otherUser: {
        id: 'dance_queen',
        username: 'dance_queen',
        display_name: 'ราชินีเต้น',
        avatar: '💃',
        online: false
      },
      lastMessage: 'เต้นเพลงนี้ยังไงคะ?',
      lastMessageTime: 'เมื่อวาน',
      unreadCount: 0,
      updated_at: new Date(Date.now() - 86400000)
    },
    {
      id: 3,
      participants: ['current_user', 'tech_reviewer'],
      otherUser: {
        id: 'tech_reviewer',
        username: 'tech_reviewer',
        display_name: 'เทครีวิว',
        avatar: '📱',
        online: true
      },
      lastMessage: 'ขอบคุณสำหรับรีวิวนะครับ',
      lastMessageTime: '2 วัน',
      unreadCount: 1,
      updated_at: new Date(Date.now() - 172800000)
    }
  ];

  const mockMessages = {
    1: [
      {
        id: 1,
        sender_id: 'chef_nong',
        message: 'สวัสดีครับ! ดูวิดีโอผัดไทยแล้วน่าอร่อยมาก',
        created_at: new Date(Date.now() - 3600000),
        is_own: false
      },
      {
        id: 2,
        sender_id: 'current_user',
        message: 'ขอบคุณครับ! ลองทำตามดูนะ',
        created_at: new Date(Date.now() - 3500000),
        is_own: true
      },
      {
        id: 3,
        sender_id: 'chef_nong',
        message: 'ได้ครับ จะลองทำให้ดู แล้วจะมาอัพเดทอีกนะ',
        created_at: new Date(Date.now() - 3400000),
        is_own: false
      },
      {
        id: 4,
        sender_id: 'chef_nong',
        message: 'สูตรผัดไทยอร่อยมาก! ครอบครัวชอบมากเลย',
        created_at: new Date(Date.now() - 1800000),
        is_own: false
      }
    ]
  };

  useEffect(() => {
    if (isAuthenticated) {
      loadChatRooms();
    }
  }, [isAuthenticated]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const loadChatRooms = async () => {
    try {
      setLoading(true);
      // Mock loading chat rooms
      setChatRooms(mockChatRooms);
    } catch (error) {
      console.error('Failed to load chat rooms:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadMessages = async (chatId) => {
    try {
      setLoading(true);
      // Mock loading messages
      const chatMessages = mockMessages[chatId] || [];
      setMessages(chatMessages);
    } catch (error) {
      console.error('Failed to load messages:', error);
    } finally {
      setLoading(false);
    }
  };

  const selectChat = (chat) => {
    setSelectedChat(chat);
    loadMessages(chat.id);
    // Mark as read
    setChatRooms(prev => prev.map(room => 
      room.id === chat.id ? { ...room, unreadCount: 0 } : room
    ));
  };

  const sendMessage = async (e) => {
    e.preventDefault();
    if (!newMessage.trim() || !selectedChat) return;

    const messageData = {
      id: Date.now(),
      sender_id: 'current_user',
      message: newMessage.trim(),
      created_at: new Date(),
      is_own: true
    };

    setMessages(prev => [...prev, messageData]);
    setNewMessage('');

    // Update last message in chat rooms
    setChatRooms(prev => prev.map(room => 
      room.id === selectedChat.id 
        ? { ...room, lastMessage: messageData.message, lastMessageTime: 'ตอนนี้' }
        : room
    ));

    try {
      // Mock sending message to API
      console.log('Sending message:', messageData);
    } catch (error) {
      console.error('Failed to send message:', error);
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const formatTime = (date) => {
    return new Date(date).toLocaleTimeString('th-TH', {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const formatLastSeen = (time) => {
    const now = new Date();
    const messageTime = new Date(time);
    const diffHours = Math.floor((now - messageTime) / (1000 * 60 * 60));
    
    if (diffHours < 1) return 'ตอนนี้';
    if (diffHours < 24) return `${diffHours} ชั่วโมงที่แล้ว`;
    if (diffHours < 48) return 'เมื่อวาน';
    return `${Math.floor(diffHours / 24)} วันที่แล้ว`;
  };

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-black text-white flex items-center justify-center">
        <div className="text-center">
          <div className="text-6xl mb-4">🔒</div>
          <h2 className="text-2xl font-bold mb-2">เข้าสู่ระบบเพื่อใช้แชท</h2>
          <p className="text-gray-400">กรุณาเข้าสู่ระบบเพื่อส่งข้อความ</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-black text-white flex">
      {/* Chat List Sidebar */}
      <div className={`${selectedChat ? 'hidden md:block' : 'block'} w-full md:w-1/3 border-r border-gray-800`}>
        {/* Header */}
        <div className="p-4 border-b border-gray-800">
          <h2 className="text-xl font-bold">💬 ข้อความ</h2>
        </div>

        {/* Chat Rooms List */}
        <div className="overflow-y-auto">
          {loading && chatRooms.length === 0 ? (
            <div className="flex items-center justify-center py-12">
              <div className="text-center">
                <div className="text-4xl mb-2">⏳</div>
                <p className="text-gray-400">กำลังโหลด...</p>
              </div>
            </div>
          ) : chatRooms.length === 0 ? (
            <div className="flex items-center justify-center py-12">
              <div className="text-center">
                <div className="text-6xl mb-4">💬</div>
                <h3 className="text-xl font-bold mb-2">ยังไม่มีข้อความ</h3>
                <p className="text-gray-400">เริ่มสนทนากับเพื่อนๆ ของคุณ</p>
              </div>
            </div>
          ) : (
            chatRooms.map((chat) => (
              <div
                key={chat.id}
                onClick={() => selectChat(chat)}
                className={`flex items-center p-4 hover:bg-gray-900 cursor-pointer transition-all border-b border-gray-800 ${
                  selectedChat?.id === chat.id ? 'bg-gray-900' : ''
                }`}
              >
                <div className="relative">
                  <div className="w-12 h-12 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full flex items-center justify-center text-white font-bold text-xl">
                    {chat.otherUser.avatar}
                  </div>
                  {chat.otherUser.online && (
                    <div className="absolute -bottom-1 -right-1 w-4 h-4 bg-green-500 rounded-full border-2 border-black"></div>
                  )}
                </div>

                <div className="flex-1 ml-3 min-w-0">
                  <div className="flex items-center justify-between">
                    <h3 className="font-bold text-white truncate">{chat.otherUser.display_name}</h3>
                    <span className="text-xs text-gray-400 flex-shrink-0 ml-2">{chat.lastMessageTime}</span>
                  </div>
                  <p className="text-sm text-gray-400 truncate">{chat.lastMessage}</p>
                </div>

                {chat.unreadCount > 0 && (
                  <div className="ml-2 bg-gradient-to-r from-purple-600 to-pink-600 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center font-bold">
                    {chat.unreadCount}
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </div>

      {/* Chat Window */}
      <div className={`${selectedChat ? 'block' : 'hidden md:block'} flex-1 flex flex-col`}>
        {selectedChat ? (
          <>
            {/* Chat Header */}
            <div className="p-4 border-b border-gray-800 flex items-center">
              <button
                onClick={() => setSelectedChat(null)}
                className="md:hidden mr-3 text-gray-400 hover:text-white"
              >
                ←
              </button>
              
              <div className="relative">
                <div className="w-10 h-10 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full flex items-center justify-center text-white font-bold">
                  {selectedChat.otherUser.avatar}
                </div>
                {selectedChat.otherUser.online && (
                  <div className="absolute -bottom-1 -right-1 w-3 h-3 bg-green-500 rounded-full border-2 border-black"></div>
                )}
              </div>

              <div className="ml-3">
                <h3 className="font-bold text-white">{selectedChat.otherUser.display_name}</h3>
                <p className="text-sm text-gray-400">
                  {selectedChat.otherUser.online ? 'ออนไลน์' : `เข้าใช้ล่าสุด ${formatLastSeen(selectedChat.updated_at)}`}
                </p>
              </div>

              <div className="ml-auto flex space-x-2">
                <button className="p-2 text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg transition-all">
                  📞
                </button>
                <button className="p-2 text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg transition-all">
                  🎥
                </button>
                <button className="p-2 text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg transition-all">
                  ⚙️
                </button>
              </div>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {loading ? (
                <div className="flex items-center justify-center py-8">
                  <div className="text-center">
                    <div className="text-4xl mb-2">⏳</div>
                    <p className="text-gray-400">กำลังโหลดข้อความ...</p>
                  </div>
                </div>
              ) : (
                messages.map((message) => (
                  <div
                    key={message.id}
                    className={`flex ${message.is_own ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`max-w-xs lg:max-w-md px-4 py-2 rounded-2xl ${
                        message.is_own
                          ? 'bg-gradient-to-r from-purple-600 to-pink-600 text-white'
                          : 'bg-gray-800 text-white'
                      }`}
                    >
                      <p className="text-sm">{message.message}</p>
                      <p className={`text-xs mt-1 ${message.is_own ? 'text-purple-100' : 'text-gray-400'}`}>
                        {formatTime(message.created_at)}
                      </p>
                    </div>
                  </div>
                ))
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Message Input */}
            <form onSubmit={sendMessage} className="p-4 border-t border-gray-800">
              <div className="flex items-end space-x-3">
                <button
                  type="button"
                  className="p-2 text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg transition-all"
                >
                  📎
                </button>
                
                <div className="flex-1 bg-gray-800 rounded-2xl px-4 py-2 flex items-center">
                  <input
                    type="text"
                    value={newMessage}
                    onChange={(e) => setNewMessage(e.target.value)}
                    placeholder="พิมพ์ข้อความ..."
                    className="flex-1 bg-transparent text-white placeholder-gray-400 focus:outline-none"
                  />
                  <button
                    type="button"
                    className="ml-2 text-gray-400 hover:text-white transition-all"
                  >
                    😊
                  </button>
                </div>

                <button
                  type="submit"
                  disabled={!newMessage.trim()}
                  className={`p-2 rounded-lg transition-all ${
                    newMessage.trim()
                      ? 'bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white'
                      : 'text-gray-400 bg-gray-800'
                  }`}
                >
                  📤
                </button>
              </div>
            </form>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center">
              <div className="text-6xl mb-4">💬</div>
              <h3 className="text-xl font-bold mb-2">เลือกแชทเพื่อเริ่มสนทนา</h3>
              <p className="text-gray-400">เลือกบทสนทนาจากรายการด้านซ้าย</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ChatPage;