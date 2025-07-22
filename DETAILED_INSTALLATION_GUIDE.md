# 🎯 Pego Installation Guide - ทีละขั้นตอนแบบ Hands-On

## 📋 สารบัญ
- [ขั้นตอน 0: การเตรียมตัว](#ขั้นตอน-0-การเตรียมตัว)
- [ขั้นตอน 1: ติดตั้งเครื่องมือพื้นฐาน](#ขั้นตอน-1-ติดตั้งเครื่องมือพื้นฐาน)
- [ขั้นตอน 2: Export Code จาก Emergent](#ขั้นตอน-2-export-code-จาก-emergent)
- [ขั้นตอน 3: Setup Database](#ขั้นตอน-3-setup-database)
- [ขั้นตอน 4: Deploy Backend](#ขั้นตอน-4-deploy-backend)
- [ขั้นตอน 5: สร้าง React Native App](#ขั้นตอน-5-สร้าง-react-native-app)
- [ขั้นตอน 6: Test บน Device](#ขั้นตอน-6-test-บน-device)
- [ขั้นตอน 7: Build สำหรับ Store](#ขั้นตอน-7-build-สำหรับ-store)
- [ขั้นตอน 8: App Store Submission](#ขั้นตอน-8-app-store-submission)

---

## ⚠️ สำคัญ: ก่อนเริ่ม ให้อ่านข้อมูลจาก Support Agent

**Emergent ปัจจุบันไม่รองรับ Native Mobile Apps โดยตรง** 

### ตัวเลือกที่เป็นไปได้:

1. **PWA to Native** - ใช้เครื่องมือแปลง PWA ไปเป็น Native (Capacitor)
2. **React Native** - Export code และพัฒนา Native App ใหม่
3. **Hybrid Approach** - ใช้ Backend API ของ Pego + สร้าง Mobile Frontend ใหม่

---

## ขั้นตอน 0: การเตรียมตัว

### 🔍 ตรวจสอบสิ่งที่ต้องมี:

**💻 Hardware Requirements:**
- **Mac**: สำหรับพัฒนา iOS (บังคับ)
- **Windows/Linux**: ได้สำหรับ Android เท่านั้น
- **RAM**: อย่างน้อย 8GB (แนะนำ 16GB)
- **Storage**: อย่างน้อย 50GB ว่าง
- **Internet**: ความเร็วดี สำหรับ download dependencies

**📱 Devices:**
- **iPhone**: สำหรับ test iOS app
- **Android Phone**: สำหรับ test Android app

**💳 Accounts Required:**
- **Apple Developer Account**: $99/ปี
- **Google Play Console**: $25 ครั้งเดียว
- **GitHub Account**: ฟรี
- **MongoDB Atlas**: ฟรี tier
- **Cloud Service**: AWS/DigitalOcean/Railway

---

## ขั้นตอน 1: ติดตั้งเครื่องมือพื้นฐาน

### 🍎 สำหรับ macOS (iOS + Android Development):

#### **1.1 Install Homebrew:**
```bash
# เปิด Terminal แล้วรันคำสั่งนี้
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# ตรวจสอบว่าติดตั้งสำเร็จ
brew --version
# ควรเห็น: Homebrew 4.x.x
```

#### **1.2 Install Node.js:**
```bash
# Install Node.js version 18 (LTS)
brew install node@18

# เพิ่ม path
echo 'export PATH="/opt/homebrew/opt/node@18/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc

# ตรวจสอบ
node --version
# ควรเห็น: v18.x.x

npm --version
# ควรเห็น: 9.x.x
```

#### **1.3 Install Xcode:**
```bash
# ดาวน์โหลดจาก Mac App Store (ใหญ่มาก ~15GB)
# หรือไปที่ https://developer.apple.com/xcode/

# หลังติดตั้งเสร็จ รันคำสั่งนี้
sudo xcode-select --install

# ตรวจสอบ
xcodebuild -version
# ควรเห็น: Xcode 15.x
```

#### **1.4 Install Android Studio:**
```bash
# ดาวน์โหลดจาก https://developer.android.com/studio

# หลังติดตั้งเสร็จ เปิด Android Studio
# - Install Android SDK
# - Install Android Emulator
# - Create Virtual Device

# เพิ่ม environment variables
echo 'export ANDROID_HOME=$HOME/Library/Android/sdk' >> ~/.zshrc
echo 'export PATH=$PATH:$ANDROID_HOME/emulator' >> ~/.zshrc
echo 'export PATH=$PATH:$ANDROID_HOME/tools' >> ~/.zshrc
echo 'export PATH=$PATH:$ANDROID_HOME/tools/bin' >> ~/.zshrc
echo 'export PATH=$PATH:$ANDROID_HOME/platform-tools' >> ~/.zshrc
source ~/.zshrc
```

#### **1.5 Install React Native CLI:**
```bash
npm install -g @react-native-community/cli

# ตรวจสอบ
npx react-native --version
# ควรเห็น: @react-native-community/cli: 12.x.x
```

#### **1.6 Install CocoaPods:**
```bash
sudo gem install cocoapods

# ตรวจสอบ
pod --version
# ควรเห็น: 1.x.x
```

#### **1.7 Install Additional Tools:**
```bash
# Watchman (สำหรับ file watching)
brew install watchman

# Git (ถ้ายังไม่มี)
brew install git

# VS Code (แนะนำ)
brew install --cask visual-studio-code
```

### 🖥️ สำหรับ Windows (Android Development เท่านั้น):

#### **1.8 Install Chocolatey:**
```powershell
# เปิด PowerShell as Administrator
Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
```

#### **1.9 Install Node.js:**
```powershell
choco install nodejs --version=18.17.0

# ตรวจสอบ
node --version
npm --version
```

#### **1.10 Install Android Studio:**
1. ดาวน์โหลดจาก https://developer.android.com/studio
2. ติดตั้งและ setup Android SDK
3. เพิ่ม Environment Variables:
   ```
   ANDROID_HOME = C:\Users\[USERNAME]\AppData\Local\Android\Sdk
   PATH += %ANDROID_HOME%\emulator
   PATH += %ANDROID_HOME%\tools
   PATH += %ANDROID_HOME%\tools\bin
   PATH += %ANDROID_HOME%\platform-tools
   ```

#### **1.11 Install React Native CLI:**
```powershell
npm install -g @react-native-community/cli
```

---

## ขั้นตอน 2: Export Code จาก Emergent

### 📁 สร้าง Project Structure

#### **2.1 สร้าง Main Directory:**
```bash
# สร้าง folder หลัก
mkdir pego-mobile-project
cd pego-mobile-project

# สร้าง structure
mkdir -p {backend,frontend,mobile,docs,assets}
mkdir -p mobile/{ios,android,shared}

# ตรวจสอบ structure
tree .
# ควรเห็น:
# .
# ├── backend/
# ├── frontend/
# ├── mobile/
# │   ├── ios/
# │   ├── android/
# │   └── shared/
# ├── docs/
# └── assets/
```

#### **2.2 Copy Backend Files จาก Emergent:**

**วิธีที่ 1: Manual Copy (แนะนำ)**
```bash
# เข้าไปใน Emergent terminal และ copy files
# หรือใช้ VS Code ใน Emergent แล้ว copy-paste

# Files ที่ต้อง copy:
cd backend/
touch server.py
touch models.py  
touch algorithm.py
touch admin_routes.py
touch requirements.txt
touch .env.example
```

**เนื้อหาไฟล์ backend/server.py:**
```python
# Copy code จาก /app/backend/server.py ใน Emergent
# (ใช้โค้ดที่พัฒนาไว้แล้ว)
```

**เนื้อหาไฟล์ backend/requirements.txt:**
```txt
fastapi==0.104.1
uvicorn==0.24.0
motor==3.3.2
python-dotenv==1.0.0
python-multipart==0.0.6
aiofiles==23.2.1
emergentintegrations==1.2.1
pydantic==2.4.2
bcrypt==4.0.1
PyJWT==2.8.0
```

#### **2.3 Copy Frontend Files:**
```bash
cd frontend/
mkdir -p src/{components,hooks,screens,services}
mkdir -p public/{icons,screenshots}

# Copy main files
touch src/App.js
touch src/App.css
touch src/AdminDashboard.js
touch src/hooks/usePWA.js
touch src/components/PWAInstallPrompt.js
touch public/manifest.json
touch public/sw.js
touch package.json
```

#### **2.4 สร้าง Configuration Files:**

**package.json:**
```json
{
  "name": "pego-frontend",
  "version": "1.0.0",
  "private": true,
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-scripts": "5.0.1",
    "axios": "^1.5.0"
  },
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test",
    "eject": "react-scripts eject"
  },
  "browserslist": {
    "production": [">0.2%", "not dead", "not op_mini all"],
    "development": ["last 1 chrome version", "last 1 firefox version", "last 1 safari version"]
  }
}
```

**backend/.env.example:**
```env
# Database
MONGO_URL=mongodb://localhost:27017
DB_NAME=pego_development

# API Keys
STRIPE_API_KEY=sk_test_xxxxx

# App Settings
SECRET_KEY=your-secret-key-here
FRONTEND_URL=http://localhost:3000
ALGORITHM_VERSION=1.0

# Admin
ADMIN_SECRET_KEY=admin-secret-key

# File Upload
MAX_FILE_SIZE=104857600  # 100MB
UPLOAD_DIR=./uploads
```

---

## ขั้นตอน 3: Setup Database

### 🍃 MongoDB Atlas Setup

#### **3.1 สร้าง MongoDB Atlas Account:**
```bash
# 1. ไปที่ https://cloud.mongodb.com/
# 2. Sign up with Google หรือ Email
# 3. เลือก "Build a Database" → "FREE" tier
```

#### **3.2 สร้าง Cluster:**
```
Cluster Name: pego-production
Cloud Provider: AWS
Region: Asia Pacific (Singapore) - ap-southeast-1
Cluster Tier: M0 Sandbox (Free Forever)
Additional Settings: Use default
```

#### **3.3 Create Database User:**
```
Database Access → Add New Database User:
Authentication Method: Password
Username: pego-admin
Password: [Generate secure password]
Built-in Role: Atlas Admin
```

#### **3.4 Configure Network Access:**
```
Network Access → Add IP Address:
Access List Entry: 0.0.0.0/0 (Allow access from anywhere)
Comment: Allow all IPs for development
```

#### **3.5 Get Connection String:**
```
Clusters → Connect → Connect your application:
Driver: Node.js
Version: 4.1 or later
Connection String: 
mongodb+srv://pego-admin:<password>@pego-production.xxxxx.mongodb.net/?retryWrites=true&w=majority
```

#### **3.6 Test Connection:**
```bash
# Install MongoDB Compass (GUI tool)
# ดาวน์โหลดจาก https://www.mongodb.com/products/compass

# หรือ test ด้วย code
cd backend/
cat > test_db.py << 'EOF'
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def test_connection():
    # Replace with your connection string
    client = AsyncIOMotorClient("mongodb+srv://pego-admin:password@pego-production.xxxxx.mongodb.net/")
    
    try:
        # Test connection
        await client.admin.command('ping')
        print("✅ MongoDB connection successful!")
        
        # List databases
        dbs = await client.list_database_names()
        print(f"Databases: {dbs}")
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(test_connection())
EOF

# Run test
python test_db.py
```

---

## ขั้นตอน 4: Deploy Backend

### ☁️ Deploy บน Railway (วิธีง่าย)

#### **4.1 สมัคร Railway:**
```bash
# 1. ไปที่ https://railway.app/
# 2. Sign up with GitHub
# 3. Verify email

# Install Railway CLI
npm install -g @railway/cli

# Login
railway login
```

#### **4.2 Prepare Backend for Deployment:**
```bash
cd backend/

# สร้าง railway.json
cat > railway.json << 'EOF'
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
EOF

# สร้าง Procfile
echo "web: uvicorn server:app --host 0.0.0.0 --port \$PORT" > Procfile

# สร้าง runtime.txt
echo "python-3.11" > runtime.txt
```

#### **4.3 Deploy:**
```bash
# Initialize Railway project
railway init

# เลือก "Empty Project"
# ตั้งชื่อโปรเจกต์: pego-backend

# Set environment variables
railway variables set MONGO_URL="mongodb+srv://pego-admin:password@pego-production.xxxxx.mongodb.net/"
railway variables set DB_NAME="pego_production"
railway variables set SECRET_KEY="super-secret-key-for-production"
railway variables set STRIPE_API_KEY="sk_test_xxxxx"

# Deploy
railway deploy

# Get URL
railway status
# จะได้ URL: https://pego-backend-production-xxxx.up.railway.app/
```

#### **4.4 Test Deployment:**
```bash
# Test API
curl https://your-railway-url.railway.app/api/
# ควรได้: {"message":"Pego Video Contest Platform API"}

# Test admin login (จะได้ 401 error เพราะยังไม่มี admin user - ปกติ)
curl https://your-railway-url.railway.app/admin/dashboard
```

---

## ขั้นตอน 5: สร้าง React Native App

### 📱 Initialize React Native Project

#### **5.1 Create Project:**
```bash
cd mobile/

# Create React Native project
npx react-native@latest init PegoApp --template react-native-template-typescript

cd PegoApp

# ตรวจสอบว่าโปรเจกต์สร้างสำเร็จ
ls -la
# ควรเห็น: android/, ios/, src/, package.json, etc.
```

#### **5.2 Install Dependencies:**
```bash
# Navigation
npm install @react-navigation/native @react-navigation/bottom-tabs @react-navigation/stack

# Screen dependencies
npm install react-native-screens react-native-safe-area-context

# Video player
npm install react-native-video

# Image picker
npm install react-native-image-picker

# Storage
npm install @react-native-async-storage/async-storage

# HTTP client
npm install axios

# Additional utils
npm install react-native-share react-native-permissions
```

#### **5.3 iOS Setup:**
```bash
cd ios/
pod install
cd ..

# ตรวจสอบว่า pod install สำเร็จ
ls ios/
# ควรเห็น: PegoApp.xcworkspace
```

#### **5.4 Android Setup:**
```bash
# เปิดไฟล์ android/app/build.gradle
# ตรวจสอบ minSdkVersion
```

**android/app/build.gradle:**
```gradle
android {
    compileSdkVersion 34
    ndkVersion rootProject.ext.ndkVersion

    defaultConfig {
        applicationId "com.pegoapp"
        minSdkVersion 21
        targetSdkVersion 34
        versionCode 1
        versionName "1.0"
    }
    // ... rest of config
}
```

#### **5.5 Test Basic Setup:**
```bash
# Start Metro bundler
npm start

# In another terminal, run iOS
npm run ios
# หรือ
npx react-native run-ios

# In another terminal, run Android
npm run android
# หรือ
npx react-native run-android
```

**คาดหวัง:** เห็นหน้าจอ React Native ขาวๆ ที่เขียนว่า "Welcome to React Native"

---

## ขั้นตอน 6: สร้าง TikTok-Style UI

### 🎬 Create Video Feed Component

#### **6.1 Create Project Structure:**
```bash
mkdir -p src/{screens,components,services,types,utils}
mkdir -p src/components/{Video,Navigation,Common}
```

#### **6.2 Create Types:**
```typescript
// src/types/index.ts
export interface User {
  id: string;
  username: string;
  display_name: string;
  avatar: string;
  is_verified: boolean;
  follower_count: number;
}

export interface Video {
  id: string;
  title: string;
  description: string;
  video_url: string;
  thumbnail_url?: string;
  user: User;
  stats: {
    views: number;
    likes: number;
    comments: number;
    shares: number;
  };
  is_liked: boolean;
  is_following: boolean;
}
```

#### **6.3 Create API Service:**
```typescript
// src/services/api.ts
import axios from 'axios';
import { Video } from '../types';

const API_BASE_URL = 'https://your-railway-url.railway.app/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
});

export const videoAPI = {
  getPersonalizedFeed: async (userId?: string): Promise<Video[]> => {
    try {
      const response = await api.get('/feed/personalized', {
        params: { user_id: userId, limit: 10 }
      });
      return response.data.feed.map((item: any) => item.video);
    } catch (error) {
      console.error('Error fetching feed:', error);
      return [];
    }
  },

  recordInteraction: async (
    videoId: string,
    interactionType: string,
    userId?: string,
    value?: number
  ) => {
    try {
      await api.post('/interaction', {
        video_id: videoId,
        interaction_type: interactionType,
        user_id: userId,
        value: value,
      });
    } catch (error) {
      console.error('Error recording interaction:', error);
    }
  },
};
```

#### **6.4 Create Main App with Navigation:**
```typescript
// App.tsx
import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { StatusBar } from 'react-native';

// Import screens
import HomeScreen from './src/screens/HomeScreen';
import CreateScreen from './src/screens/CreateScreen';

const Tab = createBottomTabNavigator();

const App = () => {
  return (
    <SafeAreaProvider>
      <NavigationContainer>
        <StatusBar barStyle="light-content" backgroundColor="#000000" />
        <Tab.Navigator
          screenOptions={{
            headerShown: false,
            tabBarStyle: {
              backgroundColor: '#000000',
              borderTopWidth: 0,
              height: 85,
              paddingBottom: 30,
              paddingTop: 10,
            },
            tabBarActiveTintColor: '#FFFFFF',
            tabBarInactiveTintColor: '#666666',
            tabBarLabelStyle: {
              fontSize: 10,
              fontWeight: '500',
            },
          }}>
          
          <Tab.Screen
            name="Home"
            component={HomeScreen}
            options={{
              tabBarLabel: 'หน้าหลัก',
              tabBarIcon: ({ color, size }) => (
                <Text style={{ color, fontSize: 24 }}>🏠</Text>
              ),
            }}
          />
          
          <Tab.Screen
            name="Create"
            component={CreateScreen}
            options={{
              tabBarLabel: 'สร้าง',
              tabBarIcon: ({ color, size }) => (
                <Text style={{ color, fontSize: 24 }}>➕</Text>
              ),
            }}
          />
        </Tab.Navigator>
      </NavigationContainer>
    </SafeAreaProvider>
  );
};

export default App;
```

#### **6.5 Create Video Feed Screen:**
```typescript
// src/screens/HomeScreen.tsx
import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  FlatList,
  Dimensions,
  StyleSheet,
  Text,
  TouchableOpacity,
  Image,
  Alert,
} from 'react-native';
import Video from 'react-native-video';
import { Video as VideoType } from '../types';
import { videoAPI } from '../services/api';

const { height: SCREEN_HEIGHT } = Dimensions.get('window');

interface VideoCardProps {
  item: VideoType;
  isActive: boolean;
}

const VideoCard: React.FC<VideoCardProps> = ({ item, isActive }) => {
  const [isLiked, setIsLiked] = useState(item.is_liked);
  const [likeCount, setLikeCount] = useState(item.stats.likes);
  const [isPlaying, setIsPlaying] = useState(false);

  // Play video when it becomes active
  useEffect(() => {
    setIsPlaying(isActive);
  }, [isActive]);

  const handleLike = async () => {
    const newLikedState = !isLiked;
    setIsLiked(newLikedState);
    setLikeCount(prev => newLikedState ? prev + 1 : prev - 1);

    // Record interaction
    await videoAPI.recordInteraction(item.id, 'like');
  };

  const handleComment = () => {
    Alert.alert('Comments', 'Comment feature coming soon!');
  };

  const handleShare = () => {
    Alert.alert('Share', 'Share feature coming soon!');
  };

  const formatNumber = (num: number): string => {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
    return num.toString();
  };

  return (
    <View style={styles.videoContainer}>
      {/* Video Player */}
      <Video
        source={{ uri: item.video_url }}
        style={styles.video}
        resizeMode="cover"
        repeat
        paused={!isPlaying}
        muted={false}
        onLoad={() => console.log('Video loaded')}
        onError={(error) => console.error('Video error:', error)}
      />

      {/* Overlay */}
      <View style={styles.overlay}>
        {/* Left side - Video info */}
        <View style={styles.leftSide}>
          {/* User info */}
          <View style={styles.userInfo}>
            <Image source={{ uri: item.user.avatar }} style={styles.avatar} />
            <View style={styles.userDetails}>
              <Text style={styles.username}>
                {item.user.display_name}
                {item.user.is_verified && <Text style={styles.verified}> ✓</Text>}
              </Text>
              <Text style={styles.handle}>@{item.user.username}</Text>
            </View>
          </View>

          {/* Video details */}
          <Text style={styles.title}>{item.title}</Text>
          <Text style={styles.description}>{item.description}</Text>
          <Text style={styles.viewCount}>
            👁 {formatNumber(item.stats.views)} views
          </Text>
        </View>

        {/* Right side - Actions */}
        <View style={styles.rightActions}>
          <TouchableOpacity style={styles.actionButton} onPress={handleLike}>
            <Text style={styles.actionIcon}>
              {isLiked ? '❤️' : '🤍'}
            </Text>
            <Text style={styles.actionText}>{formatNumber(likeCount)}</Text>
          </TouchableOpacity>

          <TouchableOpacity style={styles.actionButton} onPress={handleComment}>
            <Text style={styles.actionIcon}>💬</Text>
            <Text style={styles.actionText}>{formatNumber(item.stats.comments)}</Text>
          </TouchableOpacity>

          <TouchableOpacity style={styles.actionButton} onPress={handleShare}>
            <Text style={styles.actionIcon}>📤</Text>
            <Text style={styles.actionText}>{formatNumber(item.stats.shares)}</Text>
          </TouchableOpacity>

          <TouchableOpacity style={styles.actionButton}>
            <Text style={styles.actionIcon}>🏆</Text>
            <Text style={styles.actionText}>30฿</Text>
          </TouchableOpacity>
        </View>
      </View>
    </View>
  );
};

const HomeScreen: React.FC = () => {
  const [videos, setVideos] = useState<VideoType[]>([]);
  const [loading, setLoading] = useState(true);
  const [currentIndex, setCurrentIndex] = useState(0);
  const flatListRef = useRef<FlatList>(null);

  useEffect(() => {
    loadVideos();
  }, []);

  const loadVideos = async () => {
    setLoading(true);
    try {
      const fetchedVideos = await videoAPI.getPersonalizedFeed();
      setVideos(fetchedVideos);
    } catch (error) {
      console.error('Error loading videos:', error);
      // Load mock data for development
      setVideos(mockVideos);
    } finally {
      setLoading(false);
    }
  };

  const onViewableItemsChanged = ({ viewableItems }: any) => {
    if (viewableItems.length > 0) {
      setCurrentIndex(viewableItems[0].index || 0);
      
      // Record view for the current video
      const currentVideo = videos[viewableItems[0].index];
      if (currentVideo) {
        videoAPI.recordInteraction(currentVideo.id, 'view');
      }
    }
  };

  const renderVideoCard = ({ item, index }: { item: VideoType; index: number }) => (
    <VideoCard item={item} isActive={index === currentIndex} />
  );

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <Text style={styles.loadingText}>Loading videos...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <FlatList
        ref={flatListRef}
        data={videos}
        renderItem={renderVideoCard}
        keyExtractor={(item) => item.id}
        pagingEnabled
        showsVerticalScrollIndicator={false}
        snapToAlignment="start"
        decelerationRate="fast"
        onViewableItemsChanged={onViewableItemsChanged}
        viewabilityConfig={{
          itemVisiblePercentThreshold: 50,
        }}
        getItemLayout={(data, index) => ({
          length: SCREEN_HEIGHT,
          offset: SCREEN_HEIGHT * index,
          index,
        })}
      />
    </View>
  );
};

// Mock data for development
const mockVideos: VideoType[] = [
  {
    id: '1',
    title: 'สอนทำอาหารไทย 🍲',
    description: 'วิธีทำผัดไทยแบบง่ายๆ ที่บ้าน #ผัดไทย #อาหารไทย',
    video_url: 'https://sample-videos.com/zip/10/mp4/SampleVideo_1280x720_1mb.mp4',
    user: {
      id: '1',
      username: 'chef_nong',
      display_name: 'เชฟน้อง 👩‍🍳',
      avatar: 'https://images.unsplash.com/photo-1494790108755-2616b612b1a8?w=150',
      is_verified: true,
      follower_count: 15600,
    },
    stats: {
      views: 125000,
      likes: 8900,
      comments: 234,
      shares: 67,
    },
    is_liked: false,
    is_following: false,
  },
  // Add more mock videos...
];

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000000',
  },
  videoContainer: {
    height: SCREEN_HEIGHT,
    position: 'relative',
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
  leftSide: {
    flex: 1,
    justifyContent: 'flex-end',
    paddingBottom: 120,
    paddingHorizontal: 20,
    paddingRight: 80,
  },
  userInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 15,
  },
  avatar: {
    width: 40,
    height: 40,
    borderRadius: 20,
    borderWidth: 2,
    borderColor: '#FFFFFF',
    marginRight: 10,
  },
  userDetails: {
    flex: 1,
  },
  username: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: 'bold',
  },
  verified: {
    color: '#1DA1F2',
  },
  handle: {
    color: '#CCCCCC',
    fontSize: 14,
  },
  title: {
    color: '#FFFFFF',
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 8,
  },
  description: {
    color: '#FFFFFF',
    fontSize: 15,
    marginBottom: 10,
    lineHeight: 20,
  },
  viewCount: {
    color: '#CCCCCC',
    fontSize: 13,
  },
  rightActions: {
    width: 70,
    justifyContent: 'flex-end',
    paddingBottom: 120,
    paddingRight: 10,
  },
  actionButton: {
    alignItems: 'center',
    marginBottom: 25,
  },
  actionIcon: {
    fontSize: 32,
    marginBottom: 6,
  },
  actionText: {
    color: '#FFFFFF',
    fontSize: 12,
    textAlign: 'center',
    fontWeight: '600',
  },
  loadingContainer: {
    flex: 1,
    backgroundColor: '#000000',
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    color: '#FFFFFF',
    fontSize: 18,
  },
});

export default HomeScreen;
```

#### **6.6 Test TikTok-Style Feed:**
```bash
# Restart the app
npm start -- --reset-cache

# Run on device
npm run ios  # or npm run android
```

**คาดหวัง:** เห็นหน้าจอดำพร้อม video feed ที่เลื่อนได้ (แม้ video จะไม่เล่นก็ตาม)

---

## ขั้นตอน 7: Test บน Device

### 📱 iOS Testing

#### **7.1 Setup iOS Development:**
```bash
# เปิด iOS project
cd ios/
open PegoApp.xcworkspace
```

**ใน Xcode:**
1. เลือก development team
2. เปลี่ยน Bundle Identifier: `com.yourname.pegoapp`
3. เชื่อมต่อ iPhone ด้วย USB
4. เลือก device และกด Run (▶️)

#### **7.2 Handle iOS Permissions:**
```xml
<!-- ios/PegoApp/Info.plist -->
<key>NSCameraUsageDescription</key>
<string>Pego needs camera access to record videos</string>
<key>NSMicrophoneUsageDescription</key>
<string>Pego needs microphone access to record audio</string>
<key>NSPhotoLibraryUsageDescription</key>
<string>Pego needs photo library access to select videos</string>
```

### 🤖 Android Testing

#### **7.3 Enable Developer Mode:**
1. ไปที่ Settings → About Phone
2. กดที่ Build Number 7 ครั้ง
3. กลับไปที่ Settings → System → Developer Options
4. เปิด USB Debugging

#### **7.4 Run on Android:**
```bash
# เชื่อมต่อ Android device
adb devices
# ควรเห็น device listed

# Run app
npm run android
```

---

## ขั้นตอน 8: Build สำหรับ Store

### 🍎 iOS App Store Build

#### **8.1 Archive iOS Build:**
```bash
# เปิด Xcode
cd ios/
open PegoApp.xcworkspace

# ใน Xcode:
# 1. เลือก Generic iOS Device
# 2. Product → Archive
# 3. รอ build เสร็จ (5-15 นาที)
# 4. Organizer จะเปิดขึ้นมา
# 5. เลือก archive → Distribute App
# 6. App Store Connect → Upload
```

#### **8.2 App Store Connect Setup:**
1. ไปที่ https://appstoreconnect.apple.com/
2. My Apps → Create New App:
   ```
   Platform: iOS
   Name: Pego - วิดีโอแข่งขันสั้น
   Primary Language: Thai
   Bundle ID: com.yourname.pegoapp
   SKU: pego-ios-001
   ```

3. กรอก App Information:
   ```
   Category: Entertainment
   Content Rating: 12+
   Price: Free
   Availability: All countries
   ```

4. เตรียม Screenshots (ต้องใช้ Simulator):
   ```bash
   # เปิด iOS Simulator
   xcrun simctl list devices
   
   # เลือก iPhone 14 Pro Max
   xcrun simctl boot "iPhone 14 Pro Max"
   
   # Run app on simulator
   npm run ios
   
   # Take screenshots ขนาด 1290×2796
   ```

### 🤖 Google Play Store Build

#### **8.3 Generate Upload Key:**
```bash
cd android/app/

# Generate upload keystore
keytool -genkeypair -v -keystore upload-keystore.keystore -alias upload -keyalg RSA -keysize 2048 -validity 10000

# จด password ที่ตั้งไว้!
```

#### **8.4 Configure Gradle:**
```bash
# android/gradle.properties
echo "MYAPP_UPLOAD_STORE_FILE=upload-keystore.keystore" >> gradle.properties
echo "MYAPP_UPLOAD_KEY_ALIAS=upload" >> gradle.properties
echo "MYAPP_UPLOAD_STORE_PASSWORD=your-keystore-password" >> gradle.properties
echo "MYAPP_UPLOAD_KEY_PASSWORD=your-key-password" >> gradle.properties
```

**android/app/build.gradle:**
```gradle
android {
    ...
    signingConfigs {
        release {
            if (project.hasProperty('MYAPP_UPLOAD_STORE_FILE')) {
                storeFile file(MYAPP_UPLOAD_STORE_FILE)
                storePassword MYAPP_UPLOAD_STORE_PASSWORD
                keyAlias MYAPP_UPLOAD_KEY_ALIAS
                keyPassword MYAPP_UPLOAD_KEY_PASSWORD
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

#### **8.5 Build Release AAB:**
```bash
cd android/
./gradlew bundleRelease

# AAB file จะอยู่ที่:
# android/app/build/outputs/bundle/release/app-release.aab
```

#### **8.6 Google Play Console:**
1. ไปที่ https://play.google.com/console/
2. Create App:
   ```
   App name: Pego - วิดีโอแข่งขันสั้น  
   Default language: Thai
   App category: Entertainment
   Target age group: Teen (13+)
   ```

3. Upload AAB file:
   - Testing → Internal Testing
   - Upload app-release.aab

---

## ขั้นตอน 9: Store Submission

### 📝 เตรียม Store Assets

#### **9.1 App Icons:**
```bash
# ใช้ tool สร้าง icon หลายขนาด
# https://appicon.co/

# Upload icon และได้:
# iOS: 1024x1024 PNG
# Android: 512x512 PNG
```

#### **9.2 Screenshots:**
**iOS (ใช้ Simulator):**
- iPhone 6.7": 1290×2796
- iPhone 6.5": 1242×2688  
- iPhone 5.5": 1242×2208

**Android:**
- Phone: 1080×1920
- 7-inch tablet: 1200×1920
- 10-inch tablet: 1920×1200

#### **9.3 App Description (Thai):**
```
ชื่อแอป: Pego - วิดีโอแข่งขันสั้น

คำอธิบายสั้น:
แพลตฟอร์มแข่งขันวิดีโอสั้น ลุ้นรางวัลใหญ่ทุกสัปดาห์

คำอธิบายยาว:
🎬 Pego - แพลตฟอร์มแข่งขันวิดีโอสั้นที่ใหญ่ที่สุดในไทย!

ร่วมสร้างสรรค์คอนเทนต์และลุ้นรางวัลไปกับชุมชนนักสร้างคอนเทนต์นับหมื่นคน

✨ ฟีเจอร์เด่น:
🎥 อัพโหลดวิดีโอสั้นสูงสุด 3 นาที
💰 เพียง 30 บาทต่อการส่งเข้าแข่งขัน
🏆 วิดีโอ Top 1,000 ได้รับรางวัล 70% ของรายได้รวม
📅 การแข่งขันใหม่ทุก 7 วัน

📱 การใช้งาน:
• เลื่อนดูวิดีโอแนวตั้งแบบ TikTok
• กดไลก์ คอมเมนต์ แชร์
• ติดตามครีเอเตอร์ที่ชื่นชอบ
• อัพโหลดวิดีโอจากกล้องหรือแกลเลอรี่

🏆 วิธีการแข่งขัน:
1. สร้างวิดีโอสั้นที่น่าสนใจ
2. จ่ายค่าเข้าร่วม 30 บาท
3. รอดูยอดวิวและ engagement
4. วิดีโอ Top 1,000 ได้รับรางวัลจริง!

เริ่มต้นเป็นนักสร้างคอนเทนต์และลุ้นรางวัลใหญ่ไปกับ Pego วันนี้!

Keywords: วิดีโอสั้น, แข่งขันวิดีโอ, ครีเอเตอร์ไทย, รางวัลใหญ่, TikTok ไทย
```

### 📤 Final Submission

#### **9.4 iOS App Store:**
1. Upload build ใน App Store Connect
2. กรอก App Information ให้ครบ
3. Upload screenshots ทุกขนาด
4. เลือก pricing (Free)
5. กดส่ง Review → รอ 1-7 วัน

#### **9.5 Google Play Store:**
1. Upload AAB ใน Play Console
2. กรอก Store Listing
3. Upload screenshots และ icons
4. ตั้งค่า Content Rating
5. Submit for Review → รอ 2-3 ชั่วโมง

---

## ✅ Launch Checklist

### 🚦 ก่อน Launch:

- [ ] Backend API ทำงานได้ปกติ
- [ ] Database setup เสร็จสมบูรณ์
- [ ] Admin dashboard เข้าได้
- [ ] Mobile app test บน device จริง
- [ ] Payment integration ทำงาน (ใช้ test key ก่อน)
- [ ] Video upload/playback ใช้งานได้
- [ ] Algorithm engine ทำงาน
- [ ] Error handling ครอบคลุม
- [ ] Performance acceptable
- [ ] Security review completed

### 🎯 หลัง Launch:

- [ ] Monitor app crashes
- [ ] Check user reviews
- [ ] Monitor backend performance
- [ ] Track key metrics (DAU, retention)
- [ ] Plan first content update
- [ ] Prepare customer support

---

## 🆘 Troubleshooting

### ❌ ปัญหาที่พบบ่อย:

**1. Metro bundler error:**
```bash
npm start -- --reset-cache
```

**2. iOS build fails:**
```bash
cd ios/
pod install --repo-update
```

**3. Android build fails:**
```bash
cd android/
./gradlew clean
```

**4. Video not playing:**
- ตรวจสอบ video URL
- ตรวจสอบ network permissions
- ใช้ HTTPS URLs เท่านั้น

**5. API connection fails:**
- ตรวจสอบ CORS settings
- ตรวจสอบ SSL certificate
- ใช้ HTTPS สำหรับ production

---

## 🎉 คาดหวังผลลัพธ์:

### ✨ สิ่งที่จะได้:

1. **Native Mobile Apps** บน iOS และ Android
2. **Backend API** พร้อม algorithm engine
3. **Admin Dashboard** สำหรับจัดการ
4. **Database** พร้อม data models
5. **Payment Integration** Stripe
6. **TikTok-style UI** เต็มรูปแบบ
7. **App Store Listings** พร้อมไปขาย

### 📊 Timeline คาดการณ์:

- **วันที่ 1-3**: Setup tools และ environment
- **วันที่ 4-7**: Export code และ deploy backend
- **วันที่ 8-14**: พัฒนา React Native app
- **วันที่ 15-21**: Testing และ debugging
- **วันที่ 22-28**: Build และ submit stores
- **วันที่ 29-35**: รอ review และ launch! 🚀

**รวม: 5 สัปดาห์ถึง Pego จะขายได้ใน App Store!** 🎉