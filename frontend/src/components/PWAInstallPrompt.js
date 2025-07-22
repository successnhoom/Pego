import React, { useState } from 'react';
import { usePWA } from '../hooks/usePWA';

const PWAInstallPrompt = () => {
  const { installApp, isInstallable, isInstalled, updateAvailable, updateApp } = usePWA();
  const [showPrompt, setShowPrompt] = useState(true);

  // Don't show if already installed or not installable
  if (isInstalled || !isInstallable || !showPrompt) {
    return null;
  }

  const handleInstall = async () => {
    const success = await installApp();
    if (success) {
      setShowPrompt(false);
    }
  };

  const handleDismiss = () => {
    setShowPrompt(false);
  };

  return (
    <div className="fixed bottom-0 left-0 right-0 bg-gradient-to-r from-purple-600 to-pink-600 text-white p-4 shadow-lg z-50 transform transition-transform duration-300">
      <div className="max-w-md mx-auto flex items-center justify-between">
        <div className="flex-1">
          <div className="flex items-center mb-2">
            <span className="text-2xl mr-2">📱</span>
            <h3 className="font-bold text-lg">ติดตั้ง Pego</h3>
          </div>
          <p className="text-sm text-purple-100">
            ติดตั้งแอป Pego บนหน้าจอหลักเพื่อประสบการณ์ที่ดีที่สุด!
          </p>
        </div>
        <div className="flex flex-col gap-2 ml-4">
          <button
            onClick={handleInstall}
            className="bg-white text-purple-600 px-4 py-2 rounded-lg font-medium text-sm hover:bg-purple-50 transition-colors"
          >
            ติดตั้ง
          </button>
          <button
            onClick={handleDismiss}
            className="text-purple-200 text-sm hover:text-white transition-colors"
          >
            ไว้ก่อน
          </button>
        </div>
      </div>
    </div>
  );
};

// PWA Update Prompt
export const PWAUpdatePrompt = () => {
  const { updateAvailable, updateApp } = usePWA();
  const [showUpdate, setShowUpdate] = useState(updateAvailable);

  if (!updateAvailable || !showUpdate) {
    return null;
  }

  const handleUpdate = () => {
    updateApp();
  };

  const handleDismiss = () => {
    setShowUpdate(false);
  };

  return (
    <div className="fixed top-4 left-4 right-4 bg-green-500 text-white p-4 rounded-lg shadow-lg z-50">
      <div className="flex items-center justify-between">
        <div className="flex items-center">
          <span className="text-xl mr-2">🔄</span>
          <div>
            <h3 className="font-bold">อัปเดตใหม่พร้อม!</h3>
            <p className="text-sm text-green-100">
              มีฟีเจอร์และปรับปรุงใหม่
            </p>
          </div>
        </div>
        <div className="flex gap-2">
          <button
            onClick={handleUpdate}
            className="bg-white text-green-600 px-3 py-1 rounded font-medium text-sm hover:bg-green-50"
          >
            อัปเดต
          </button>
          <button
            onClick={handleDismiss}
            className="text-green-200 text-sm hover:text-white"
          >
            ×
          </button>
        </div>
      </div>
    </div>
  );
};

// Offline Indicator
export const OfflineIndicator = () => {
  const { isOnline } = usePWA();

  if (isOnline) {
    return null;
  }

  return (
    <div className="fixed top-0 left-0 right-0 bg-orange-500 text-white text-center py-2 z-50">
      <div className="flex items-center justify-center">
        <span className="mr-2">📶</span>
        <span className="font-medium">กำลังทำงานแบบออฟไลน์</span>
      </div>
    </div>
  );
};

export default PWAInstallPrompt;