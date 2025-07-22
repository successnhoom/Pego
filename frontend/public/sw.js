// Pego PWA Service Worker
const CACHE_NAME = 'pego-v1.0.0';
const urlsToCache = [
  '/',
  '/static/js/bundle.js',
  '/static/css/main.css',
  '/manifest.json',
  // Cache Google Fonts
  'https://fonts.googleapis.com/css2?family=Sarabun:wght@300;400;500;600;700&display=swap',
  // Cache hero images
  'https://images.unsplash.com/photo-1686399237674-2de90fb2d25e',
  'https://images.unsplash.com/photo-1741949438476-c0d07192cb11'
];

// Install Service Worker
self.addEventListener('install', (event) => {
  console.log('🚀 Pego PWA Service Worker installing...');
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('📦 Caching Pego app resources');
        return cache.addAll(urlsToCache.map(url => {
          // Handle potential CORS issues with external images
          if (url.startsWith('https://images.unsplash.com')) {
            return new Request(url, { mode: 'cors' });
          }
          return url;
        }));
      })
      .catch((error) => {
        console.error('❌ Cache installation failed:', error);
      })
  );
  // Skip waiting to activate immediately
  self.skipWaiting();
});

// Activate Service Worker
self.addEventListener('activate', (event) => {
  console.log('✅ Pego PWA Service Worker activated');
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME) {
            console.log('🗑 Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
  // Take control of all pages immediately
  self.clients.claim();
});

// Fetch Strategy: Network First with Cache Fallback for API calls
// Cache First for static assets
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Handle API calls with Network First strategy
  if (request.url.includes('/api/')) {
    event.respondWith(
      fetch(request)
        .then((response) => {
          // Clone response for caching
          const responseClone = response.clone();
          
          // Cache successful GET requests
          if (request.method === 'GET' && response.ok) {
            caches.open(CACHE_NAME).then((cache) => {
              cache.put(request, responseClone);
            });
          }
          
          return response;
        })
        .catch(() => {
          // Return cached version if network fails
          return caches.match(request).then((cachedResponse) => {
            if (cachedResponse) {
              return cachedResponse;
            }
            // Return offline page for failed API calls
            return new Response(
              JSON.stringify({ 
                message: 'ขณะนี้แอปทำงานแบบออฟไลน์', 
                offline: true 
              }),
              {
                status: 200,
                headers: { 'Content-Type': 'application/json' }
              }
            );
          });
        })
    );
    return;
  }

  // Handle static assets with Cache First strategy
  if (
    request.destination === 'script' ||
    request.destination === 'style' ||
    request.destination === 'image' ||
    request.url.includes('fonts.googleapis.com') ||
    request.url.includes('images.unsplash.com')
  ) {
    event.respondWith(
      caches.match(request).then((cachedResponse) => {
        if (cachedResponse) {
          return cachedResponse;
        }
        
        return fetch(request).then((response) => {
          // Don't cache if not ok
          if (!response.ok) {
            return response;
          }
          
          const responseClone = response.clone();
          caches.open(CACHE_NAME).then((cache) => {
            cache.put(request, responseClone);
          });
          
          return response;
        });
      })
    );
    return;
  }

  // Default: Network First for other requests
  event.respondWith(
    fetch(request).catch(() => {
      return caches.match(request).then((cachedResponse) => {
        return cachedResponse || caches.match('/');
      });
    })
  );
});

// Background Sync for failed uploads (future feature)
self.addEventListener('sync', (event) => {
  console.log('🔄 Background sync:', event.tag);
  
  if (event.tag === 'video-upload') {
    event.waitUntil(
      // Handle background upload sync
      handleBackgroundUpload()
    );
  }
});

async function handleBackgroundUpload() {
  // Future: Handle failed video uploads when back online
  console.log('📤 Processing background video upload...');
}

// Push notification handler (future feature)
self.addEventListener('push', (event) => {
  if (!event.data) return;

  const options = {
    body: event.data.text(),
    icon: '/icons/icon-192x192.png',
    badge: '/icons/badge-72x72.png',
    vibrate: [200, 100, 200],
    data: {
      dateOfArrival: Date.now(),
      primaryKey: '2'
    },
    actions: [
      {
        action: 'explore',
        title: 'ดูวิดีโอใหม่',
        icon: '/icons/play-icon-24x24.png'
      },
      {
        action: 'close',
        title: 'ปิด',
        icon: '/icons/close-icon-24x24.png'
      }
    ]
  };

  event.waitUntil(
    self.registration.showNotification('🎬 Pego', options)
  );
});

// Notification click handler
self.addEventListener('notificationclick', (event) => {
  event.notification.close();

  if (event.action === 'explore') {
    event.waitUntil(
      clients.openWindow('/')
    );
  } else if (event.action === 'close') {
    // Notification closed
  } else {
    // Default action - open app
    event.waitUntil(
      clients.openWindow('/')
    );
  }
});

console.log('🎬 Pego PWA Service Worker loaded successfully!');