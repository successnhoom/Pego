import React, { useState } from 'react';
import { GoogleLogin } from '@react-oauth/google';
import { useAuth } from '../contexts/AuthContext';

const LoginModal = ({ isOpen, onClose }) => {
  const { loginWithGoogle, sendOTP, verifyOTP, loading } = useAuth();
  const [loginMethod, setLoginMethod] = useState('google'); // 'google' or 'phone'
  const [phone, setPhone] = useState('');
  const [otp, setOtp] = useState('');
  const [otpSent, setOtpSent] = useState(false);
  const [countdown, setCountdown] = useState(0);

  if (!isOpen) return null;

  const handleGoogleSuccess = async (credentialResponse) => {
    const result = await loginWithGoogle(credentialResponse.credential);
    if (result.success) {
      onClose();
    }
  };

  const handleGoogleError = () => {
    console.error('Google login failed');
  };

  const handleSendOTP = async (e) => {
    e.preventDefault();
    if (!phone.trim()) return;

    const result = await sendOTP(phone);
    if (result.success) {
      setOtpSent(true);
      // Start countdown
      setCountdown(60);
      const timer = setInterval(() => {
        setCountdown((prev) => {
          if (prev <= 1) {
            clearInterval(timer);
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    }
  };

  const handleVerifyOTP = async (e) => {
    e.preventDefault();
    if (!otp.trim()) return;

    const result = await verifyOTP(phone, otp);
    if (result.success) {
      onClose();
    }
  };

  const resetForm = () => {
    setPhone('');
    setOtp('');
    setOtpSent(false);
    setCountdown(0);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-md w-full p-6 relative">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-gray-500 hover:text-gray-700 text-2xl"
        >
          ×
        </button>

        {/* Header */}
        <div className="text-center mb-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">เข้าสู่ระบบ Pego</h2>
          <p className="text-gray-600">เลือกวิธีการเข้าสู่ระบบ</p>
        </div>

        {/* Login Method Tabs */}
        <div className="flex mb-6 bg-gray-100 rounded-lg p-1">
          <button
            onClick={() => {
              setLoginMethod('google');
              resetForm();
            }}
            className={`flex-1 py-2 px-4 rounded-md font-medium transition-all ${
              loginMethod === 'google'
                ? 'bg-white text-blue-600 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            🌐 Google
          </button>
          <button
            onClick={() => {
              setLoginMethod('phone');
              resetForm();
            }}
            className={`flex-1 py-2 px-4 rounded-md font-medium transition-all ${
              loginMethod === 'phone'
                ? 'bg-white text-blue-600 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            📱 เบอร์โทร
          </button>
        </div>

        {/* Google OAuth Login */}
        {loginMethod === 'google' && (
          <div className="space-y-4">
            <div className="flex justify-center">
              <GoogleLogin
                onSuccess={handleGoogleSuccess}
                onError={handleGoogleError}
                text="signin_with"
                shape="rectangular"
                theme="outline"
                size="large"
                width="100%"
              />
            </div>
            <p className="text-sm text-gray-500 text-center">
              เข้าสู่ระบบด้วย Google Account ของคุณ
            </p>
          </div>
        )}

        {/* Phone OTP Login */}
        {loginMethod === 'phone' && (
          <div className="space-y-4">
            {!otpSent ? (
              <form onSubmit={handleSendOTP} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    หมายเลขโทรศัพท์
                  </label>
                  <input
                    type="tel"
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    placeholder="0812345678"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900"
                    required
                  />
                </div>
                <button
                  type="submit"
                  disabled={loading || !phone.trim()}
                  className={`w-full py-3 px-4 rounded-md font-medium transition-all ${
                    loading || !phone.trim()
                      ? 'bg-gray-300 cursor-not-allowed text-gray-500'
                      : 'bg-blue-600 hover:bg-blue-700 text-white'
                  }`}
                >
                  {loading ? 'กำลังส่ง...' : 'ส่งรหัส OTP'}
                </button>
              </form>
            ) : (
              <form onSubmit={handleVerifyOTP} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    รหัส OTP
                  </label>
                  <input
                    type="text"
                    value={otp}
                    onChange={(e) => setOtp(e.target.value)}
                    placeholder="123456"
                    maxLength="6"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent text-center text-2xl tracking-widest text-gray-900"
                    required
                  />
                  <p className="text-sm text-gray-600 mt-2">
                    รหัส OTP ถูกส่งไปที่ {phone}
                  </p>
                </div>
                
                <button
                  type="submit"
                  disabled={loading || !otp.trim()}
                  className={`w-full py-3 px-4 rounded-md font-medium transition-all ${
                    loading || !otp.trim()
                      ? 'bg-gray-300 cursor-not-allowed text-gray-500'
                      : 'bg-green-600 hover:bg-green-700 text-white'
                  }`}
                >
                  {loading ? 'กำลังยืนยัน...' : 'เข้าสู่ระบบ'}
                </button>

                <div className="flex justify-between items-center">
                  <button
                    type="button"
                    onClick={() => {
                      setOtpSent(false);
                      setOtp('');
                    }}
                    className="text-sm text-blue-600 hover:text-blue-800"
                  >
                    ← เปลี่ยนเบอร์
                  </button>
                  
                  {countdown > 0 ? (
                    <span className="text-sm text-gray-500">
                      ส่งใหม่ได้ในอีก {countdown} วินาที
                    </span>
                  ) : (
                    <button
                      type="button"
                      onClick={handleSendOTP}
                      className="text-sm text-blue-600 hover:text-blue-800"
                    >
                      ส่งรหัสใหม่
                    </button>
                  )}
                </div>
              </form>
            )}
          </div>
        )}

        {/* Footer */}
        <div className="mt-6 text-center text-sm text-gray-500">
          การเข้าสู่ระบบแสดงว่าคุณยอมรับ
          <br />
          <a href="#" className="text-blue-600 hover:text-blue-800">
            ข้อกำหนดการใช้งาน
          </a>{' '}
          และ{' '}
          <a href="#" className="text-blue-600 hover:text-blue-800">
            นโยบายความเป็นส่วนตัว
          </a>
        </div>
      </div>
    </div>
  );
};

export default LoginModal;