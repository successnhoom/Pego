# 🚀 Pego Complete Deployment Guide
## การติดตั้งและขึ้น App Store/Play Store ทีละขั้นตอน

---

## 📋 สารบัญ

1. [การเตรียมความพร้อม](#1-การเตรียมความพร้อม)
2. [Export Code จาก Emergent](#2-export-code-จาก-emergent)
3. [Setup Backend บน Cloud](#3-setup-backend-บน-cloud)
4. [React Native Development](#4-react-native-development)
5. [Native App Features](#5-native-app-features)
6. [App Store Submission](#6-app-store-submission)
7. [Play Store Submission](#7-play-store-submission)
8. [Admin Dashboard Deployment](#8-admin-dashboard-deployment)

---

## 1. การเตรียมความพร้อม

### 🔧 เครื่องมือที่ต้องติดตั้ง

#### **บน macOS (สำหรับ iOS development):**
```bash
# 1. Install Xcode
# ดาวน์โหลดจาก Mac App Store

# 2. Install Command Line Tools
xcode-select --install

# 3. Install CocoaPods
sudo gem install cocoapods

# 4. Install Node.js (version 18+)
# ดาวน์โหลดจาก https://nodejs.org/

# 5. Install React Native CLI
npm install -g @react-native-community/cli

# 6. Install Watchman
brew install watchman
```

#### **บน Windows/Linux (สำหรับ Android development):**
```bash
# 1. Install Node.js (version 18+)
# ดาวน์โหลดจาก https://nodejs.org/

# 2. Install Android Studio
# ดาวน์โหลดจาก https://developer.android.com/studio

# 3. Install Java Development Kit (JDK 11)
# ดาวน์โหลดจาก https://adoptium.net/

# 4. Install React Native CLI
npm install -g @react-native-community/cli
```

### 📱 Developer Accounts

#### **Apple Developer Account:**
1. ไปที่ https://developer.apple.com/programs/
2. สมัครสมาชิก ($99/ปี)
3. รอการอนุมัติ 1-2 วัน

#### **Google Play Console:**
1. ไปที่ https://play.google.com/console/
2. จ่ายค่าสมัคร $25 (ครั้งเดียว)
3. สร้าง developer account

---

## 2. Export Code จาก Emergent

### 📁 ขั้นตอนการ Export

#### **2.1 Export Frontend Code:**
```bash
# สร้าง folder สำหรับโปรเจกต์
mkdir pego-mobile-app
cd pego-mobile-app

# สร้าง folder structure
mkdir frontend backend docs assets
```

#### **2.2 Copy Frontend Files:**
จาก Emergent `/app/frontend/` copy ไฟล์เหล่านี้:

```
frontend/
├── src/
│   ├── App.js              # Main TikTok-style app
│   ├── App.css             # TikTok styles
│   ├── AdminDashboard.js   # Admin interface
│   ├── hooks/
│   │   └── usePWA.js       # PWA hooks
│   └── components/
│       └── PWAInstallPrompt.js
├── public/
│   ├── manifest.json       # PWA manifest
│   ├── sw.js              # Service worker
│   └── offline.html       # Offline page
└── package.json           # Dependencies
```

#### **2.3 Copy Backend Files:**
จาก Emergent `/app/backend/` copy ไฟล์เหล่านี้:

```
backend/
├── server.py              # Main FastAPI server
├── models.py              # Database models
├── algorithm.py           # Recommendation engine
├── admin_routes.py        # Admin API routes
├── requirements.txt       # Python dependencies
└── .env.example          # Environment template
```

#### **2.4 สร้าง Environment Files:**
```bash
# Backend environment
cp backend/.env backend/.env.production

# แก้ไขค่าต่างๆ ใน .env.production
nano backend/.env.production
```

```env
# backend/.env.production
MONGO_URL=mongodb+srv://username:password@cluster.mongodb.net/pego
DB_NAME=pego_production
STRIPE_API_KEY=sk_live_xxxxx  # Live key สำหรับ production
FRONTEND_URL=https://pego.app
SECRET_KEY=your-super-secret-key-here
ALGORITHM_VERSION=1.0
```

---

## 3. Setup Backend บน Cloud

### ☁️ Deploy Backend API

#### **Option 1: Deploy บน DigitalOcean (แนะนำ)**

```bash
# 1. สร้าง Droplet
# - Ubuntu 22.04 LTS
# - 2GB RAM, 1 CPU
# - $12/month

# 2. เชื่อมต่อ SSH
ssh root@your-server-ip

# 3. ติดตั้ง Python และ dependencies
apt update
apt install -y python3 python3-pip nginx certbot python3-certbot-nginx

# 4. Clone โปรเจกต์
git clone your-repo-url /app
cd /app/backend

# 5. ติดตั้ง Python packages
pip3 install -r requirements.txt

# 6. สร้าง systemd service
nano /etc/systemd/system/pego-api.service
```

```ini
[Unit]
Description=Pego FastAPI application
After=network.target

[Service]
User=root
Group=root
WorkingDirectory=/app/backend
Environment="PATH=/usr/local/bin"
ExecStart=/usr/local/bin/uvicorn server:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# 7. เริ่มต้น service
systemctl daemon-reload
systemctl enable pego-api
systemctl start pego-api

# 8. ตั้งค่า Nginx
nano /etc/nginx/sites-available/pego-api
```

```nginx
server {
    listen 80;
    server_name api.pego.app;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
# 9. เปิดใช้งาน site
ln -s /etc/nginx/sites-available/pego-api /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx

# 10. ติดตั้ง SSL
certbot --nginx -d api.pego.app
```

#### **Option 2: Deploy บน Railway (ง่ายกว่า)**

```bash
# 1. Install Railway CLI
npm install -g @railway/cli

# 2. Login to Railway
railway login

# 3. Deploy backend
cd backend
railway deploy
```

### 🗄️ Setup Database

#### **MongoDB Atlas Setup:**
1. ไปที่ https://cloud.mongodb.com/
2. สร้าง account ฟรี
3. สร้าง cluster ใหม่:
   ```
   Cluster Name: pego-production
   Region: Asia-Pacific (Singapore)
   Tier: M0 (Free)
   ```

4. สร้าง Database User:
   ```
   Username: pego-admin
   Password: [generate strong password]
   Role: Atlas Admin
   ```

5. เพิ่ม IP Whitelist:
   ```
   0.0.0.0/0 (Allow access from anywhere)
   ```

6. ได้ Connection String:
   ```
   mongodb+srv://pego-admin:password@pego-production.xxxxx.mongodb.net/
   ```

#### **Initialize Database:**
```bash
# สร้าง script สำหรับ setup database
nano setup_database.py
```

```python
# setup_database.py
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from models import AdminUser, AlgorithmConfig, Competition
from datetime import datetime, timedelta
import bcrypt
import uuid

async def setup_database():
    # Connect to MongoDB
    client = AsyncIOMotorClient("your-mongodb-url")
    db = client["pego_production"]
    
    # Create admin user
    admin_password = bcrypt.hashpw("admin123".encode(), bcrypt.gensalt()).decode()
    admin_user = AdminUser(
        username="admin",
        email="admin@pego.app",
        password_hash=admin_password,
        role="super_admin",
        permissions=["all"]
    )
    
    await db.admin_users.insert_one(admin_user.dict())
    
    # Create default algorithm config
    algorithm_config = AlgorithmConfig(
        name="Production Algorithm v1.0",
        version="1.0",
        is_active=True
    )
    
    await db.algorithm_configs.insert_one(algorithm_config.dict())
    
    # Create first competition
    competition = Competition(
        title="Pego Launch Competition 🚀",
        description="การแข่งขันเปิดตัว Pego แพลตฟอร์มวิดีโอสั้น",
        start_date=datetime.utcnow(),
        end_date=datetime.utcnow() + timedelta(days=7),
        status="active",
        created_by=admin_user.id
    )
    
    await db.competitions.insert_one(competition.dict())
    
    print("✅ Database setup completed!")
    print(f"Admin username: admin")
    print(f"Admin password: admin123")
    print("🔒 Please change the password after first login!")

if __name__ == "__main__":
    asyncio.run(setup_database())
```

```bash
# รัน setup script
python3 setup_database.py
```

---

## 4. React Native Development

### 📱 สร้าง React Native App

#### **4.1 Initialize Project:**
```bash
# สร้าง React Native project
npx react-native init PegoApp --template react-native-template-typescript

cd PegoApp

# ติดตั้ง dependencies
npm install @react-navigation/native @react-navigation/bottom-tabs
npm install react-native-screens react-native-safe-area-context
npm install react-native-video react-native-image-picker
npm install @react-native-async-storage/async-storage
npm install react-native-share react-native-camera
```

#### **4.2 iOS Setup:**
```bash
cd ios
pod install
cd ..
```

#### **4.3 Android Setup:**
แก้ไข `android/app/build.gradle`:
```gradle
android {
    ...
    defaultConfig {
        ...
        minSdkVersion 21
        targetSdkVersion 33
    }
}
```

### 🎬 แปลง TikTok UI เป็น React Native

#### **4.4 สร้าง Main App Structure:**
```javascript
// App.tsx
import React from 'react';
import {NavigationContainer} from '@react-navigation/native';
import {createBottomTabNavigator} from '@react-navigation/bottom-tabs';
import {StatusBar} from 'react-native';

// Import screens (จะสร้างต่อไป)
import HomeScreen from './src/screens/HomeScreen';
import DiscoverScreen from './src/screens/DiscoverScreen';
import CreateScreen from './src/screens/CreateScreen';
import InboxScreen from './src/screens/InboxScreen';
import ProfileScreen from './src/screens/ProfileScreen';

const Tab = createBottomTabNavigator();

const App = () => {
  return (
    <NavigationContainer>
      <StatusBar barStyle="light-content" backgroundColor="#000" />
      <Tab.Navigator
        screenOptions={{
          headerShown: false,
          tabBarStyle: {
            backgroundColor: '#000',
            borderTopColor: '#333',
          },
          tabBarActiveTintColor: '#fff',
          tabBarInactiveTintColor: '#666',
        }}>
        <Tab.Screen 
          name="Home" 
          component={HomeScreen}
          options={{
            tabBarIcon: ({color}) => <Text style={{color}}>🏠</Text>,
          }}
        />
        <Tab.Screen 
          name="Discover" 
          component={DiscoverScreen}
          options={{
            tabBarIcon: ({color}) => <Text style={{color}}>🔍</Text>,
          }}
        />
        <Tab.Screen 
          name="Create" 
          component={CreateScreen}
          options={{
            tabBarIcon: ({color}) => <Text style={{color}}>➕</Text>,
          }}
        />
        <Tab.Screen 
          name="Inbox" 
          component={InboxScreen}
          options={{
            tabBarIcon: ({color}) => <Text style={{color}}>💬</Text>,
          }}
        />
        <Tab.Screen 
          name="Profile" 
          component={ProfileScreen}
          options={{
            tabBarIcon: ({color}) => <Text style={{color}}>👤</Text>,
          }}
        />
      </Tab.Navigator>
    </NavigationContainer>
  );
};

export default App;
```

#### **4.5 สร้าง TikTok-style Video Feed:**
```javascript
// src/screens/HomeScreen.tsx
import React, {useState, useEffect, useRef} from 'react';
import {
  View,
  FlatList,
  Dimensions,
  StyleSheet,
  Text,
  TouchableOpacity,
  Image,
} from 'react-native';
import Video from 'react-native-video';

const {height: SCREEN_HEIGHT, width: SCREEN_WIDTH} = Dimensions.get('window');

interface VideoItem {
  id: string;
  title: string;
  description: string;
  video_url: string;
  user: {
    username: string;
    display_name: string;
    avatar: string;
    is_verified: boolean;
  };
  stats: {
    views: number;
    likes: number;
    comments: number;
    shares: number;
  };
  is_liked: boolean;
}

const VideoCard: React.FC<{item: VideoItem; isActive: boolean}> = ({
  item,
  isActive,
}) => {
  const [isPlaying, setIsPlaying] = useState(isActive);
  const [isLiked, setIsLiked] = useState(item.is_liked);

  const handleLike = () => {
    setIsLiked(!isLiked);
    // TODO: API call to like/unlike video
  };

  return (
    <View style={styles.videoContainer}>
      {/* Video Player */}
      <Video
        source={{uri: item.video_url}}
        style={styles.video}
        resizeMode="cover"
        repeat
        paused={!isPlaying}
        muted={false}
      />

      {/* Overlay Content */}
      <View style={styles.overlay}>
        {/* Bottom Left - User Info */}
        <View style={styles.bottomLeft}>
          <View style={styles.userInfo}>
            <Image source={{uri: item.user.avatar}} style={styles.avatar} />
            <View>
              <Text style={styles.username}>
                {item.user.display_name}
                {item.user.is_verified && <Text style={styles.verified}> ✓</Text>}
              </Text>
              <Text style={styles.handle}>@{item.user.username}</Text>
            </View>
          </View>
          
          <Text style={styles.title}>{item.title}</Text>
          <Text style={styles.description}>{item.description}</Text>
          <Text style={styles.viewCount}>
            👁 {formatNumber(item.stats.views)} ครั้ง
          </Text>
        </View>

        {/* Right Side - Action Buttons */}
        <View style={styles.rightActions}>
          <TouchableOpacity style={styles.actionButton} onPress={handleLike}>
            <Text style={[styles.actionIcon, isLiked && styles.liked]}>
              {isLiked ? '❤️' : '🤍'}
            </Text>
            <Text style={styles.actionCount}>
              {formatNumber(item.stats.likes)}
            </Text>
          </TouchableOpacity>

          <TouchableOpacity style={styles.actionButton}>
            <Text style={styles.actionIcon}>💬</Text>
            <Text style={styles.actionCount}>
              {formatNumber(item.stats.comments)}
            </Text>
          </TouchableOpacity>

          <TouchableOpacity style={styles.actionButton}>
            <Text style={styles.actionIcon}>📤</Text>
            <Text style={styles.actionCount}>
              {formatNumber(item.stats.shares)}
            </Text>
          </TouchableOpacity>

          <TouchableOpacity style={styles.actionButton}>
            <Text style={styles.actionIcon}>🏆</Text>
            <Text style={styles.actionCount}>30฿</Text>
          </TouchableOpacity>
        </View>
      </View>
    </View>
  );
};

const HomeScreen: React.FC = () => {
  const [videos, setVideos] = useState<VideoItem[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const flatListRef = useRef<FlatList>(null);

  useEffect(() => {
    fetchVideos();
  }, []);

  const fetchVideos = async () => {
    try {
      // TODO: Replace with actual API call
      const response = await fetch('https://api.pego.app/api/feed/personalized');
      const data = await response.json();
      setVideos(data.feed);
    } catch (error) {
      console.error('Error fetching videos:', error);
      // Use mock data for development
      setVideos(mockVideos);
    }
  };

  const onViewableItemsChanged = ({viewableItems}: any) => {
    if (viewableItems.length > 0) {
      setCurrentIndex(viewableItems[0].index);
    }
  };

  const renderItem = ({item, index}: {item: VideoItem; index: number}) => (
    <VideoCard item={item} isActive={index === currentIndex} />
  );

  return (
    <View style={styles.container}>
      <FlatList
        ref={flatListRef}
        data={videos}
        renderItem={renderItem}
        keyExtractor={(item) => item.id}
        pagingEnabled
        showsVerticalScrollIndicator={false}
        snapToAlignment="start"
        decelerationRate="fast"
        onViewableItemsChanged={onViewableItemsChanged}
        viewabilityConfig={{
          itemVisiblePercentThreshold: 50,
        }}
      />
    </View>
  );
};

const formatNumber = (num: number): string => {
  if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
  if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
  return num.toString();
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000',
  },
  videoContainer: {
    height: SCREEN_HEIGHT,
    width: SCREEN_WIDTH,
  },
  video: {
    position: 'absolute',
    top: 0,
    left: 0,
    bottom: 0,
    right: 0,
  },
  overlay: {
    flex: 1,
    flexDirection: 'row',
  },
  bottomLeft: {
    flex: 1,
    justifyContent: 'flex-end',
    paddingBottom: 120,
    paddingLeft: 20,
    paddingRight: 80,
  },
  userInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 10,
  },
  avatar: {
    width: 40,
    height: 40,
    borderRadius: 20,
    borderWidth: 2,
    borderColor: '#fff',
    marginRight: 10,
  },
  username: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  verified: {
    color: '#1DA1F2',
  },
  handle: {
    color: '#ccc',
    fontSize: 14,
  },
  title: {
    color: '#fff',
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 5,
  },
  description: {
    color: '#fff',
    fontSize: 14,
    marginBottom: 10,
  },
  viewCount: {
    color: '#ccc',
    fontSize: 12,
  },
  rightActions: {
    width: 60,
    justifyContent: 'flex-end',
    paddingBottom: 120,
    paddingRight: 10,
  },
  actionButton: {
    alignItems: 'center',
    marginBottom: 20,
  },
  actionIcon: {
    fontSize: 28,
    marginBottom: 5,
  },
  liked: {
    transform: [{scale: 1.2}],
  },
  actionCount: {
    color: '#fff',
    fontSize: 12,
    textAlign: 'center',
  },
});

export default HomeScreen;
```

---

## 5. Native App Features

### 📷 Camera Integration

#### **5.1 ติดตั้ง Camera Dependencies:**
```bash
npm install react-native-image-picker react-native-permissions
cd ios && pod install && cd ..
```

#### **5.2 iOS Permissions (ios/PegoApp/Info.plist):**
```xml
<key>NSCameraUsageDescription</key>
<string>Pego needs camera access to record videos</string>
<key>NSMicrophoneUsageDescription</key>
<string>Pego needs microphone access to record audio</string>
<key>NSPhotoLibraryUsageDescription</key>
<string>Pego needs photo library access to select videos</string>
```

#### **5.3 Android Permissions (android/app/src/main/AndroidManifest.xml):**
```xml
<uses-permission android:name="android.permission.CAMERA" />
<uses-permission android:name="android.permission.RECORD_AUDIO" />
<uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE" />
<uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE" />
```

#### **5.4 Create Video Recorder Screen:**
```javascript
// src/screens/CreateScreen.tsx
import React, {useState} from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Alert,
  TextInput,
} from 'react-native';
import {launchCamera, launchImageLibrary} from 'react-native-image-picker';

const CreateScreen: React.FC = () => {
  const [videoUri, setVideoUri] = useState<string | null>(null);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');

  const selectVideo = () => {
    Alert.alert(
      'Select Video',
      'Choose video source',
      [
        {text: 'Camera', onPress: recordVideo},
        {text: 'Library', onPress: selectFromLibrary},
        {text: 'Cancel', style: 'cancel'},
      ]
    );
  };

  const recordVideo = () => {
    launchCamera(
      {
        mediaType: 'video',
        videoQuality: 'high',
        durationLimit: 180, // 3 minutes max
      },
      (response) => {
        if (response.assets && response.assets[0]) {
          setVideoUri(response.assets[0].uri!);
        }
      }
    );
  };

  const selectFromLibrary = () => {
    launchImageLibrary(
      {
        mediaType: 'video',
      },
      (response) => {
        if (response.assets && response.assets[0]) {
          setVideoUri(response.assets[0].uri!);
        }
      }
    );
  };

  const uploadVideo = async () => {
    if (!videoUri || !title) {
      Alert.alert('Error', 'Please select video and enter title');
      return;
    }

    try {
      const formData = new FormData();
      formData.append('file', {
        uri: videoUri,
        type: 'video/mp4',
        name: 'video.mp4',
      } as any);

      // First, initiate upload and get payment URL
      const response = await fetch('https://api.pego.app/api/upload/initiate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          title,
          description,
          user_id: 'current_user_id', // TODO: Get from auth
        }),
      });

      const data = await response.json();
      
      // TODO: Open payment URL in WebView or external browser
      // After payment success, upload the actual video file
      
      Alert.alert('Success', 'Video upload initiated! Please complete payment.');
    } catch (error) {
      Alert.alert('Error', 'Upload failed');
    }
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>สร้างวิดีโอใหม่</Text>
      
      {!videoUri ? (
        <TouchableOpacity style={styles.selectButton} onPress={selectVideo}>
          <Text style={styles.selectButtonText}>📹 เลือกวิดีโอ</Text>
        </TouchableOpacity>
      ) : (
        <View style={styles.form}>
          <Text style={styles.selectedText}>✅ เลือกวิดีโอแล้ว</Text>
          
          <TextInput
            style={styles.input}
            placeholder="ชื่อวิดีโอ"
            placeholderTextColor="#666"
            value={title}
            onChangeText={setTitle}
          />
          
          <TextInput
            style={[styles.input, styles.textArea]}
            placeholder="คำอธิบาย"
            placeholderTextColor="#666"
            value={description}
            onChangeText={setDescription}
            multiline
            numberOfLines={4}
          />
          
          <TouchableOpacity style={styles.uploadButton} onPress={uploadVideo}>
            <Text style={styles.uploadButtonText}>อัพโหลด (30฿)</Text>
          </TouchableOpacity>
        </View>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000',
    padding: 20,
    justifyContent: 'center',
  },
  title: {
    color: '#fff',
    fontSize: 24,
    fontWeight: 'bold',
    textAlign: 'center',
    marginBottom: 40,
  },
  selectButton: {
    backgroundColor: '#7c3aed',
    padding: 20,
    borderRadius: 15,
    alignItems: 'center',
  },
  selectButtonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: 'bold',
  },
  form: {
    marginTop: 20,
  },
  selectedText: {
    color: '#10b981',
    textAlign: 'center',
    marginBottom: 20,
    fontSize: 16,
  },
  input: {
    backgroundColor: '#1a1a1a',
    color: '#fff',
    padding: 15,
    borderRadius: 10,
    marginBottom: 15,
    fontSize: 16,
  },
  textArea: {
    height: 100,
    textAlignVertical: 'top',
  },
  uploadButton: {
    backgroundColor: '#ec4899',
    padding: 20,
    borderRadius: 15,
    alignItems: 'center',
    marginTop: 20,
  },
  uploadButtonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: 'bold',
  },
});

export default CreateScreen;
```

### 📱 Push Notifications

#### **5.5 Setup Push Notifications:**
```bash
npm install @react-native-firebase/app @react-native-firebase/messaging
cd ios && pod install && cd ..
```

---

## 6. App Store Submission

### 🍎 iOS App Store

#### **6.1 Prepare iOS Build:**
```bash
cd ios

# Update bundle identifier in XCode
# com.pego.app

# Update version and build number
# Version: 1.0.0
# Build: 1

# Archive build
xcodebuild -workspace PegoApp.xcworkspace -scheme PegoApp archive
```

#### **6.2 App Store Connect Setup:**
1. ไปที่ https://appstoreconnect.apple.com/
2. คลิก "My Apps" → "+" → "New App"
3. กรอกข้อมูล:
   ```
   Name: Pego - วิดีโอแข่งขันสั้น
   Primary Language: Thai
   Bundle ID: com.pego.app
   SKU: pego-ios-001
   ```

#### **6.3 App Information:**
```
App Name: Pego
Subtitle: แพลตฟอร์มแข่งขันวิดีโอสั้น
Category: Entertainment
Content Rating: 12+

Description:
🎬 Pego - แพลตฟอร์มแข่งขันวิดีโอสั้นที่ใหญ่ที่สุดในไทย

✨ ฟีเจอร์เด่น:
• อัพโหลดวิดีโอสั้นสูงสุด 3 นาที
• ลุ้นรางวัลใหญ่ทุกสัปดาห์
• เพียง 30 บาทต่อการส่งเข้าแข่งขัน
• วิดีโอ Top 1,000 ได้รับรางวัล 70% ของรายได้รวม

📱 การใช้งาน:
• เลื่อนดูวิดีโอแนวตั้งเหมือน TikTok
• กดไลก์, คอมเมนต์, แชร์
• ติดตามผู้สร้างคอนเทนต์ที่ชอบ
• สร้างและอัพโหลดวิดีโอของคุณเอง

🏆 ระบบการแข่งขัน:
• การแข่งขันใหม่ทุก 7 วัน
• ชนะตามยอดวิว และ engagement
• รางวัลแจกจริงทุกรอบ

เริ่มต้นเป็นนักสร้างคอนเทนต์และลุ้นรางวัลใหญ่ไปกับ Pego วันนี้!
```

#### **6.4 Screenshots Required:**
- iPhone 6.7" (iPhone 14 Pro Max): 1290×2796 pixels
- iPhone 6.5" (iPhone 14 Plus): 1242×2688 pixels  
- iPhone 5.5" (iPhone 8 Plus): 1242×2208 pixels
- iPad Pro 12.9": 2048×2732 pixels

#### **6.5 Upload Build:**
```bash
# Use Xcode Organizer or Application Loader
# Upload .ipa file to App Store Connect
```

---

## 7. Play Store Submission

### 🤖 Google Play Store

#### **7.1 Prepare Android Build:**
```bash
cd android

# Generate upload key
keytool -genkeypair -v -keystore upload-keystore.keystore -alias upload -keyalg RSA -keysize 2048 -validity 10000

# Add to android/gradle.properties
echo "UPLOAD_STORE_FILE=upload-keystore.keystore" >> gradle.properties
echo "UPLOAD_KEY_ALIAS=upload" >> gradle.properties
echo "UPLOAD_STORE_PASSWORD=your-password" >> gradle.properties
echo "UPLOAD_KEY_PASSWORD=your-password" >> gradle.properties
```

#### **7.2 Update build.gradle:**
```gradle
// android/app/build.gradle
android {
    ...
    signingConfigs {
        release {
            if (project.hasProperty('UPLOAD_STORE_FILE')) {
                storeFile file(UPLOAD_STORE_FILE)
                storePassword UPLOAD_STORE_PASSWORD
                keyAlias UPLOAD_KEY_ALIAS
                keyPassword UPLOAD_KEY_PASSWORD
            }
        }
    }
    buildTypes {
        release {
            ...
            signingConfig signingConfigs.release
        }
    }
}
```

#### **7.3 Build Release APK:**
```bash
cd android
./gradlew assembleRelease

# AAB file will be at:
# android/app/build/outputs/bundle/release/app-release.aab
```

#### **7.4 Play Console Setup:**
1. ไปที่ https://play.google.com/console/
2. คลิก "Create app"
3. กรอกข้อมูล:
   ```
   App name: Pego - วิดีโอแข่งขันสั้น
   Default language: Thai
   App or game: App
   Free or paid: Free
   ```

#### **7.5 Store Listing:**
```
Short description:
แพลตฟอร์มแข่งขันวิดีโอสั้น ลุ้นรางวัลใหญ่ทุกสัปดาห์

Full description:
🎬 Pego - แพลตฟอร์มแข่งขันวิดีโอสั้นที่ใหญ่ที่สุดในไทย

ร่วมสร้างสรรค์คอนเทนต์และลุ้นรางวัลไปกับชุมชนนักสร้างคอนเทนต์นับหมื่นคน!

✨ ทำไมต้องเลือก Pego?
🎥 อัพโหลดวิดีโอสั้นสูงสุด 3 นาที
💰 เพียง 30 บาทต่อการส่งเข้าแข่งขัน
🏆 วิดีโอ Top 1,000 ได้รับรางวัล 70% ของรายได้รวม
📅 การแข่งขันใหม่ทุก 7 วัน

📱 ฟีเจอร์ที่คุณจะได้:
• เลื่อนดูวิดีโอแนวตั้งแบบ TikTok
• กดไลก์, คอมเมนต์, แชร์ได้ง่ายๆ
• ติดตามครีเอเตอร์ที่ชื่นชอบ
• อัพโหลดวิดีโอจากกล้องหรือแกลเลอรี่
• ระบบแจ้งเตือนการแข่งขันใหม่

🏆 วิธีการแข่งขัน:
1. สร้างวิดีโอสั้นที่น่าสนใจ
2. จ่ายค่าเข้าร่วม 30 บาท
3. รอดูยอดวิวและ engagement
4. วิดีโอ Top 1,000 ได้รับรางวัลจริง!

💡 เคล็ดลับการชนะ:
• สร้างเนื้อหาที่น่าสนใจและติดตาม
• ใช้แฮชแท็กที่เป็นกระแส
• โต้ตอบกับผู้ชมและครีเอเตอร์คนอื่นๆ
• อัพโหลดในช่วงเวลาที่คนดูเยอะ

🎯 เหมาะสำหรับ:
• นักสร้างคอนเทนต์มือใหม่และมืออาชีพ
• คนที่ชอบดูและแชร์วิดีโอสั้น
• ผู้ที่ต้องการสร้างรายได้จากความสามารถ
• ชุมชนคนรักความบันเทิง

📞 ติดต่อเรา:
• อีเมล: support@pego.app
• เว็บไซต์: https://pego.app

เริ่มต้นเส้นทางนักสร้างคอนเทนต์และลุ้นรางวัลใหญ่ไปกับ Pego วันนี้!

#วิดีโอสั้น #แข่งขันวิดีโอ #ครีเอเตอร์ไทย #รางวัลใหญ่
```

#### **7.6 Upload APK/AAB:**
```bash
# Upload app-release.aab to Play Console
# Set up release tracks (Internal testing → Closed testing → Open testing → Production)
```

---

## 8. Admin Dashboard Deployment

### 🔧 Deploy Admin Panel

#### **8.1 Create Separate Admin Build:**
```bash
# สร้าง admin-specific build
cd frontend
npm install

# สร้าง environment สำหรับ admin
echo "REACT_APP_BACKEND_URL=https://api.pego.app" > .env.production
echo "REACT_APP_ADMIN_MODE=true" >> .env.production

npm run build
```

#### **8.2 Deploy Admin Dashboard:**
```bash
# Deploy บน Netlify
npm install -g netlify-cli
netlify deploy --prod --dir=build

# หรือ Deploy บน Vercel
npm install -g vercel
vercel --prod
```

#### **8.3 Setup Custom Domain:**
```bash
# ตั้งค่า DNS records:
# admin.pego.app → CNAME → your-netlify-site.netlify.app
```

#### **8.4 Create First Admin User:**
```python
# create_admin.py
import asyncio
import bcrypt
from motor.motor_asyncio import AsyncIOMotorClient
from models import AdminUser

async def create_admin():
    client = AsyncIOMotorClient("your-mongodb-url")
    db = client["pego_production"]
    
    password_hash = bcrypt.hashpw("secure-admin-password".encode(), bcrypt.gensalt()).decode()
    
    admin = AdminUser(
        username="admin",
        email="admin@pego.app",
        password_hash=password_hash,
        role="super_admin",
        permissions=["all"]
    )
    
    await db.admin_users.insert_one(admin.dict())
    print("✅ Admin user created!")
    print("Username: admin")
    print("Password: secure-admin-password")
    print("🔒 Please change password after first login!")

asyncio.run(create_admin())
```

---

## 9. Go Live Checklist

### ✅ Pre-Launch Checklist

#### **9.1 Backend Checklist:**
- [ ] API deployed and accessible
- [ ] Database setup with indexes
- [ ] Admin user created
- [ ] SSL certificates installed
- [ ] Environment variables configured
- [ ] Payment integration tested
- [ ] Algorithm engine working
- [ ] File upload limits configured
- [ ] Error monitoring setup

#### **9.2 Mobile App Checklist:**
- [ ] iOS build signed and uploaded
- [ ] Android build signed and uploaded
- [ ] All permissions configured
- [ ] App icons and splash screens ready
- [ ] Store listings complete with screenshots
- [ ] Privacy policy and terms of service links
- [ ] App ratings and content warnings set
- [ ] Test devices verified functionality

#### **9.3 Admin Dashboard Checklist:**
- [ ] Admin panel deployed
- [ ] SSL certificate installed
- [ ] Admin authentication working
- [ ] All admin features functional
- [ ] Logging and monitoring setup
- [ ] Backup procedures in place

### 🚀 Launch Day Tasks

#### **9.4 Launch Sequence:**
1. **Deploy Backend** (2-3 hours before)
2. **Deploy Admin Dashboard** (1-2 hours before)  
3. **Submit iOS App** (Submit for review - takes 1-7 days)
4. **Submit Android App** (Can be live in 2-3 hours)
5. **Test all systems end-to-end**
6. **Create first competition**
7. **Announce launch** 🎉

#### **9.5 Post-Launch Monitoring:**
```bash
# Monitor API logs
tail -f /var/log/pego-api.log

# Monitor database performance
# Check MongoDB Atlas metrics

# Monitor app store reviews
# Check App Store Connect and Play Console
```

---

## 📞 Support & Next Steps

### 🔧 Ongoing Maintenance

#### **Monthly Tasks:**
- Monitor app performance and crash reports
- Update dependencies and security patches
- Review algorithm performance and adjust weights
- Analyze user engagement metrics
- Plan new features based on user feedback

#### **Feature Roadmap Ideas:**
- Live streaming capabilities
- Advanced video editing tools
- Sponsored content system
- Creator fund program
- Advanced analytics for creators
- Multi-language support
- AI-powered content moderation

### 📚 Documentation Links
- [React Native Documentation](https://reactnative.dev/docs/getting-started)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [MongoDB Atlas](https://docs.atlas.mongodb.com/)
- [App Store Guidelines](https://developer.apple.com/app-store/guidelines/)
- [Play Store Policies](https://support.google.com/googleplay/android-developer/answer/9859348)

---

## 🎯 Success Metrics to Track

### KPIs to Monitor:
- **User Acquisition**: Downloads, registrations
- **Engagement**: Daily/Monthly active users, session duration  
- **Content**: Videos uploaded per day, completion rates
- **Revenue**: Competition entries, total revenue per round
- **Retention**: Day 1, Day 7, Day 30 retention rates

### Analytics Tools:
- Google Analytics for web traffic
- Firebase Analytics for mobile app usage
- MongoDB analytics for database performance
- Custom dashboards in admin panel

---

**🎉 ขอให้การ launch สำเร็จลุล่วง! Pego พร้อมไปพิชิต App Store และ Play Store แล้ว! 🚀**