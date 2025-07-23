import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';
import toast from 'react-hot-toast';

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState(localStorage.getItem('token'));

  const API_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001/api';

  // Configure axios defaults
  useEffect(() => {
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    } else {
      delete axios.defaults.headers.common['Authorization'];
    }
  }, [token]);

  // Load user data on mount
  useEffect(() => {
    const loadUser = async () => {
      if (token) {
        try {
          const response = await axios.get(`${API_URL}/auth/me`);
          setUser(response.data.user);
        } catch (error) {
          console.error('Failed to load user:', error);
          // Token might be expired
          logout();
        }
      }
      setLoading(false);
    };

    loadUser();
  }, [token]);

  // Login with Google OAuth
  const loginWithGoogle = async (googleToken) => {
    try {
      setLoading(true);
      const response = await axios.post(`${API_URL}/auth/google`, {
        google_token: googleToken
      });

      const { user: userData, access_token } = response.data;
      
      localStorage.setItem('token', access_token);
      setToken(access_token);
      setUser(userData);
      
      toast.success(`ยินดีต้อนรับ ${userData.display_name}!`);
      return { success: true, user: userData };
    } catch (error) {
      const errorMsg = error.response?.data?.detail || 'เข้าสู่ระบบล้มเหลว';
      toast.error(errorMsg);
      return { success: false, error: errorMsg };
    } finally {
      setLoading(false);
    }
  };

  // Send OTP to phone
  const sendOTP = async (phone) => {
    try {
      setLoading(true);
      const response = await axios.post(`${API_URL}/auth/phone/send-otp`, {
        phone: phone
      });

      toast.success('รหัส OTP ถูกส่งแล้ว');
      return { success: true, data: response.data };
    } catch (error) {
      const errorMsg = error.response?.data?.detail || 'ส่ง OTP ล้มเหลว';
      toast.error(errorMsg);
      return { success: false, error: errorMsg };
    } finally {
      setLoading(false);
    }
  };

  // Verify OTP and login
  const verifyOTP = async (phone, otpCode) => {
    try {
      setLoading(true);
      const response = await axios.post(`${API_URL}/auth/phone/verify`, {
        phone: phone,
        otp_code: otpCode
      });

      const { user: userData, access_token } = response.data;
      
      localStorage.setItem('token', access_token);
      setToken(access_token);
      setUser(userData);
      
      toast.success(`ยินดีต้อนรับ ${userData.display_name}!`);
      return { success: true, user: userData };
    } catch (error) {
      const errorMsg = error.response?.data?.detail || 'ยืนยัน OTP ล้มเหลว';
      toast.error(errorMsg);
      return { success: false, error: errorMsg };
    } finally {
      setLoading(false);
    }
  };

  // Update user profile
  const updateProfile = async (profileData) => {
    try {
      setLoading(true);
      const response = await axios.put(`${API_URL}/auth/profile`, profileData);
      
      setUser(response.data.user);
      toast.success('อัพเดทโปรไฟล์สำเร็จ');
      return { success: true, user: response.data.user };
    } catch (error) {
      const errorMsg = error.response?.data?.detail || 'อัพเดทโปรไฟล์ล้มเหลว';
      toast.error(errorMsg);
      return { success: false, error: errorMsg };
    } finally {
      setLoading(false);
    }
  };

  // Get credit balance
  const getCreditBalance = async () => {
    try {
      const response = await axios.get(`${API_URL}/credits/balance`);
      return { success: true, credits: response.data.credits };
    } catch (error) {
      const errorMsg = error.response?.data?.detail || 'ไม่สามารถโหลดเครดิตได้';
      return { success: false, error: errorMsg };
    }
  };

  // Top up credits
  const topUpCredits = async (amount, paymentMethod = 'promptpay') => {
    try {
      setLoading(true);
      const response = await axios.post(`${API_URL}/credits/topup`, {
        amount: amount,
        payment_method: paymentMethod
      });

      return { success: true, data: response.data };
    } catch (error) {
      const errorMsg = error.response?.data?.detail || 'เติมเงินล้มเหลว';
      toast.error(errorMsg);
      return { success: false, error: errorMsg };
    } finally {
      setLoading(false);
    }
  };

  // Confirm PromptPay payment
  const confirmPromptPayPayment = async (sessionId) => {
    try {
      setLoading(true);
      const response = await axios.post(`${API_URL}/credits/confirm/promptpay/${sessionId}`);
      
      // Refresh user data to get updated credits
      const userResponse = await axios.get(`${API_URL}/auth/me`);
      setUser(userResponse.data.user);
      
      toast.success(`เติมเงินสำเร็จ! +${response.data.credits_added} เครดิต`);
      return { success: true, data: response.data };
    } catch (error) {
      const errorMsg = error.response?.data?.detail || 'ยืนยันการชำระเงินล้มเหลว';
      toast.error(errorMsg);
      return { success: false, error: errorMsg };
    } finally {
      setLoading(false);
    }
  };

  // Upload video (initiate)
  const initiateVideoUpload = async (videoData) => {
    try {
      setLoading(true);
      const response = await axios.post(`${API_URL}/upload/initiate`, videoData);
      return { success: true, data: response.data };
    } catch (error) {
      const errorMsg = error.response?.data?.detail || 'เริ่มต้นอัพโหลดล้มเหลว';
      toast.error(errorMsg);
      return { success: false, error: errorMsg };
    } finally {
      setLoading(false);
    }
  };

  // Upload video file
  const uploadVideoFile = async (videoId, file) => {
    try {
      setLoading(true);
      const formData = new FormData();
      formData.append('file', file);

      const response = await axios.post(`${API_URL}/upload/video/${videoId}`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      // Refresh user data to get updated credits
      const userResponse = await axios.get(`${API_URL}/auth/me`);
      setUser(userResponse.data.user);

      toast.success('อัพโหลดวิดีโอสำเร็จ!');
      return { success: true, data: response.data };
    } catch (error) {
      const errorMsg = error.response?.data?.detail || 'อัพโหลดวิดีโอล้มเหลว';
      toast.error(errorMsg);
      return { success: false, error: errorMsg };
    } finally {
      setLoading(false);
    }
  };

  // Logout
  const logout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
    delete axios.defaults.headers.common['Authorization'];
    toast.success('ออกจากระบบแล้ว');
  };

  const value = {
    user,
    loading,
    token,
    loginWithGoogle,
    sendOTP,
    verifyOTP,
    updateProfile,
    getCreditBalance,
    topUpCredits,
    confirmPromptPayPayment,
    initiateVideoUpload,
    uploadVideoFile,
    logout,
    isAuthenticated: !!user
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};