import { useState, useEffect } from 'react';

export const usePWA = () => {
  const [installPrompt, setInstallPrompt] = useState(null);
  const [isInstallable, setIsInstallable] = useState(false);
  const [isInstalled, setIsInstalled] = useState(false);
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [updateAvailable, setUpdateAvailable] = useState(false);

  useEffect(() => {
    // Check if app is installed (standalone mode)
    const checkInstalled = () => {
      const isStandalone = window.matchMedia('(display-mode: standalone)').matches;
      const isWebAppCapable = window.navigator.standalone;
      setIsInstalled(isStandalone || isWebAppCapable);
    };

    // Listen for install prompt
    const handleBeforeInstallPrompt = (e) => {
      e.preventDefault();
      setInstallPrompt(e);
      setIsInstallable(true);
      console.log('📱 PWA install prompt ready');
    };

    // Listen for successful installation
    const handleAppInstalled = () => {
      setIsInstalled(true);
      setInstallPrompt(null);
      setIsInstallable(false);
      console.log('✅ Pego PWA installed successfully');
    };

    // Listen for online/offline status
    const handleOnline = () => {
      setIsOnline(true);
      console.log('🌐 Back online');
    };

    const handleOffline = () => {
      setIsOnline(false);
      console.log('📶 Gone offline');
    };

    // Service Worker update detection
    const handleServiceWorkerUpdate = () => {
      setUpdateAvailable(true);
      console.log('🔄 New version available');
    };

    // Register event listeners
    window.addEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
    window.addEventListener('appinstalled', handleAppInstalled);
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    // Check initial state
    checkInstalled();

    // Register Service Worker
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker
        .register('/sw.js')
        .then((registration) => {
          console.log('🚀 Pego PWA Service Worker registered successfully');

          // Check for updates
          registration.addEventListener('updatefound', () => {
            const newWorker = registration.installing;
            if (newWorker) {
              newWorker.addEventListener('statechange', () => {
                if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                  handleServiceWorkerUpdate();
                }
              });
            }
          });
        })
        .catch((error) => {
          console.error('❌ Service Worker registration failed:', error);
        });
    }

    // Cleanup
    return () => {
      window.removeEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
      window.removeEventListener('appinstalled', handleAppInstalled);
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  const installApp = async () => {
    if (!installPrompt) return false;

    try {
      const result = await installPrompt.prompt();
      console.log('📱 Install prompt result:', result.outcome);

      if (result.outcome === 'accepted') {
        setIsInstalled(true);
        console.log('✅ User accepted the install prompt');
      } else {
        console.log('❌ User dismissed the install prompt');
      }

      setInstallPrompt(null);
      setIsInstallable(false);
      return result.outcome === 'accepted';
    } catch (error) {
      console.error('❌ Install prompt failed:', error);
      return false;
    }
  };

  const updateApp = () => {
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.ready.then((registration) => {
        if (registration.waiting) {
          registration.waiting.postMessage({ type: 'SKIP_WAITING' });
        }
      });
      window.location.reload();
    }
  };

  return {
    installApp,
    updateApp,
    isInstallable,
    isInstalled,
    isOnline,
    updateAvailable
  };
};