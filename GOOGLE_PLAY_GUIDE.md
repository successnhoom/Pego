# 📱 คู่มือการสร้าง Android App และอัพขึ้น Google Play Store

## 📋 สิ่งที่คุณต้องเตรียม

### 1. **Google Play Console Account**
- ค่าธรรมเนียม: $25 (จ่ายครั้งเดียว)
- สมัครที่: https://play.google.com/console

### 2. **Development Environment**
- Node.js 18+ 
- Android Studio
- Java Development Kit (JDK) 11+

### 3. **App Assets**
- App Icon (512x512 px)
- Feature Graphic (1024x500 px)
- Screenshots (อย่างน้อย 2 รูป)
- App Description

---

## 🔧 ขั้นตอนที่ 1: ติดตั้ง Development Tools

### ติดตั้ง Node.js
```bash
# ดาวน์โหลดจาก https://nodejs.org
# หรือใช้ nvm
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
nvm install 18
nvm use 18
```

### ติดตั้ง Android Studio
1. ดาวน์โหลดจาก: https://developer.android.com/studio
2. ติดตั้งตามขั้นตอน
3. เปิด Android Studio → Tools → SDK Manager
4. ติดตั้ง Android SDK (API 33+)

### ติดตั้ง Capacitor CLI
```bash
npm install -g @capacitor/cli
```

---

## 📦 ขั้นตอนที่ 2: เตรียม Frontend PWA

### ปรับปรุง Frontend Configuration
สร้างไฟล์ environment สำหรับ production:

```bash
cd /path/to/your/frontend
```

### สร้าง .env.production
```bash
# Production API URL (ใช้ domain ที่คุณ deploy backend)
REACT_APP_BACKEND_URL=https://yourdomain.com/api

# Google OAuth Client ID (สำหรับ Android)
REACT_APP_GOOGLE_CLIENT_ID=your-android-google-client-id

# App Configuration
REACT_APP_APP_NAME=Pego
REACT_APP_VERSION=1.0.0
```

### ปรับปรุง PWA Manifest
แก้ไขไฟล์ `public/manifest.json`:
```json
{
  "name": "Pego - Video Contest Platform",
  "short_name": "Pego",
  "description": "แพลตฟอร์มแข่งขันวิดีโอสั้นแบบ TikTok",
  "start_url": "/",
  "display": "standalone",
  "theme_color": "#000000",
  "background_color": "#000000",
  "icons": [
    {
      "src": "pwa-icons/icon-72.png",
      "sizes": "72x72",
      "type": "image/png"
    },
    {
      "src": "pwa-icons/icon-96.png", 
      "sizes": "96x96",
      "type": "image/png"
    },
    {
      "src": "pwa-icons/icon-128.png",
      "sizes": "128x128", 
      "type": "image/png"
    },
    {
      "src": "pwa-icons/icon-144.png",
      "sizes": "144x144",
      "type": "image/png"
    },
    {
      "src": "pwa-icons/icon-152.png",
      "sizes": "152x152",
      "type": "image/png"
    },
    {
      "src": "pwa-icons/icon-192.png",
      "sizes": "192x192",
      "type": "image/png"
    },
    {
      "src": "pwa-icons/icon-384.png",
      "sizes": "384x384",
      "type": "image/png"
    },
    {
      "src": "pwa-icons/icon-512.png",
      "sizes": "512x512",
      "type": "image/png"
    }
  ]
}
```

### Build Production Frontend
```bash
# Build สำหรับ production
npm run build

# ทดสอบ build
npx serve -s build
```

---

## 🤖 ขั้นตอนที่ 3: สร้าง Android App ด้วย Capacitor

### Initialize Capacitor
```bash
cd /path/to/your/frontend

# ติดตั้ง Capacitor
npm install @capacitor/core @capacitor/cli
npm install @capacitor/android

# Initialize Capacitor
npx cap init Pego com.yourcompany.pego
```

### เพิ่ม Android Platform
```bash
# เพิ่ม Android platform
npx cap add android

# Copy web assets
npx cap copy android

# Sync ไฟล์
npx cap sync android
```

### แก้ไข Capacitor Configuration
แก้ไขไฟล์ `capacitor.config.ts`:
```typescript
import { CapacitorConfig } from '@capacitor/core';

const config: CapacitorConfig = {
  appId: 'com.yourcompany.pego',
  appName: 'Pego',
  webDir: 'build',
  server: {
    androidScheme: 'https'
  },
  plugins: {
    SplashScreen: {
      launchShowDuration: 2000,
      backgroundColor: "#000000",
      showSpinner: false
    },
    StatusBar: {
      style: 'dark',
      backgroundColor: '#000000'
    }
  }
};

export default config;
```

---

## 🎨 ขั้นตอนที่ 4: เตรียม App Assets

### สร้าง App Icons
ใช้เครื่องมือออนไลน์เช่น:
- https://easyappicon.com/
- https://makeappicon.com/
- https://appicon.co/

อัปโหลดรูป 1024x1024 px แล้วดาวน์โหลด Android icon pack

### วาง Icons ในโปรเจค
```bash
# Copy icons ไปยัง Android resources
cp -r downloaded-icons/android/* android/app/src/main/res/
```

### สร้าง Splash Screen
1. สร้างรูป splash screen 2732x2732 px
2. ใส่ลงใน `android/app/src/main/res/drawable/splash.png`

---

## 🔨 ขั้นตอนที่ 5: Build Android App

### เปิด Android Studio
```bash
npx cap open android
```

### ปรับแต่งใน Android Studio

#### 1. แก้ไข `android/app/build.gradle`:
```gradle
android {
    compileSdkVersion 33
    
    defaultConfig {
        applicationId "com.yourcompany.pego"
        minSdkVersion 22
        targetSdkVersion 33
        versionCode 1
        versionName "1.0.0"
    }
    
    buildTypes {
        release {
            minifyEnabled true
            proguardFiles getDefaultProguardFile('proguard-android-optimize.txt'), 'proguard-rules.pro'
        }
    }
}
```

#### 2. แก้ไข Permissions ใน `android/app/src/main/AndroidManifest.xml`:
```xml
<uses-permission android:name="android.permission.INTERNET" />
<uses-permission android:name="android.permission.CAMERA" />
<uses-permission android:name="android.permission.RECORD_AUDIO" />
<uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE" />
<uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE" />
```

### Build APK
```bash
# ใน Android Studio:
# Build → Generate Signed Bundle/APK → Android App Bundle (AAB)
# หรือ APK

# หรือใช้ command line:
cd android
./gradlew assembleRelease
```

---

## 🔐 ขั้นตอนที่ 6: สร้าง Keystore และ Sign App

### สร้าง Signing Key
```bash
# สร้าง keystore
keytool -genkey -v -keystore pego-release-key.keystore -keyalg RSA -keysize 2048 -validity 10000 -alias pego

# ใส่ข้อมูล:
# - Password สำหรับ keystore
# - ชื่อ, องค์กร, เมือง, ประเทศ
# - Password สำหรับ key (ใช้เหมือนกับ keystore)
```

### กำหนดค่า Gradle สำหรับ Signing
สร้างไฟล์ `android/keystore.properties`:
```properties
storeFile=../pego-release-key.keystore
storePassword=your-keystore-password
keyAlias=pego
keyPassword=your-key-password
```

แก้ไข `android/app/build.gradle`:
```gradle
// ด้านบนของไฟล์
def keystorePropertiesFile = rootProject.file("keystore.properties")
def keystoreProperties = new Properties()
keystoreProperties.load(new FileInputStream(keystorePropertiesFile))

android {
    ...
    
    signingConfigs {
        release {
            keyAlias keystoreProperties['keyAlias']
            keyPassword keystoreProperties['keyPassword']
            storeFile file(keystoreProperties['storeFile'])
            storePassword keystoreProperties['storePassword']
        }
    }
    
    buildTypes {
        release {
            signingConfig signingConfigs.release
            minifyEnabled true
            proguardFiles getDefaultProguardFile('proguard-android-optimize.txt'), 'proguard-rules.pro'
        }
    }
}
```

### Build Signed AAB
```bash
cd android
./gradlew bundleRelease

# ไฟล์ AAB จะอยู่ที่: android/app/build/outputs/bundle/release/app-release.aab
```

---

## 📱 ขั้นตอนที่ 7: สมัคร Google Play Console Account

### 1. สมัครบัญชี
1. ไปที่ https://play.google.com/console
2. จ่ายค่าธรรมเนียม $25
3. กรอกข้อมูลบัญชีและการตรวจสอบตัวตน

### 2. สร้าง App ใหม่
1. คลิก "Create app"
2. เลือก "App" และ "Free"
3. ใส่ชื่อแอป: "Pego"
4. เลือกประเทศ: "Thailand"
5. เลือกประเภท: "App"

---

## 📋 ขั้นตอนที่ 8: เตรียมข้อมูลแอป

### 1. App Information
- **App name:** Pego
- **Short description:** แพลตฟอร์มแข่งขันวิดีโอสั้น
- **Full description:**
```
Pego คือแพลตฟอร์มแข่งขันวิดีโอสั้นที่ให้คุณสร้างสรรค์และแชร์วิดีโอในรูปแบบ TikTok

✨ ฟีเจอร์หลัก:
• สร้างและแชร์วิดีโอสั้น
• เข้าร่วมการแข่งขันรายสัปดาห์
• ลุ้นรับเงินรางวัล
• ระบบชำระเงินปลอดภัย
• เชื่อมต่อกับเพื่อนและผู้ติดตาม

🏆 การแข่งขัน:
• จ่าย 30 บาทต่อการอัปโหลด
• การแข่งขันทุก 7 วัน
• วิดีโอยอดนิยม Top 1,000 ได้รับเงินรางวัล 70% ของยอดรวม

💫 เริ่มต้นสร้างเนื้อหาและลุ้นรับรางวัลไปพร้อมกัน!
```

### 2. Graphics Assets
- **App icon:** 512x512 px (PNG)
- **Feature graphic:** 1024x500 px (PNG) 
- **Phone screenshots:** อย่างน้อย 2 รูป (1080x1920 px)
- **Tablet screenshots:** (ถ้ามี)

### 3. Categorization
- **Category:** Social
- **Tags:** video, social, contest, thailand

---

## 🚀 ขั้นตอนที่ 9: อัปโหลดแอป

### 1. Upload AAB File
1. ไปที่ "App releases" → "Production"
2. คลิก "Create new release"
3. อัปโหลดไฟล์ `app-release.aab`
4. ใส่ Release notes:
```
เวอร์ชันแรกของ Pego - แพลตฟอร์มแข่งขันวิดีโอสั้น

ฟีเจอร์ใหม่:
• ระบบสร้างและแชร์วิดีโอ
• การแข่งขันรายสัปดาห์
• ระบบชำระเงินและรางวัล
• การเชื่อมต่อกับผู้ใช้อื่น
```

### 2. Content Rating
1. ไปที่ "Content rating"
2. เลือก questionnaire และตอบคำถาม
3. สำหรับ Pego: เลือก "Social" category
4. ตอบว่าไม่มีเนื้อหาไม่เหมาะสม

### 3. App Content
กรอกข้อมูล:
- **Privacy Policy:** URL ของ privacy policy
- **App access:** เลือกว่าใครเข้าถึงได้บ้าง
- **Ads:** บอกว่ามีโฆษณาหรือไม่
- **Content guidelines:** ยืนยันว่าเป็นไปตาม Google's policy

### 4. Pricing & Distribution
- **Free or Paid:** Free
- **Countries:** เลือกประเทศที่ต้องการ (Thailand, อื่นๆ)
- **Device categories:** Phone and Tablet

---

## ✅ ขั้นตอนที่ 10: Review และ Publish

### 1. ตรวจสอบข้อมูล
ไปที่ "App releases" และตรวจสอบว่า:
- ✅ App bundle uploaded
- ✅ Store listing complete  
- ✅ Content rating complete
- ✅ Pricing & distribution complete

### 2. Submit for Review
1. คลิก "Review release"
2. ตรวจสอบข้อมูลทั้งหมด
3. คลิก "Start rollout to production"

### 3. รอการอนุมัติ
- Google จะใช้เวลา 1-3 วัน ในการตรวจสอบ
- คุณจะได้รับอีเมลแจ้งผลการตรวจสอบ

---

## 📊 การจัดการหลัง Launch

### 1. Monitoring
- ดูสถิติการดาวน์โหลดใน Play Console
- ตรวจสอบ reviews และ ratings
- ดู crash reports

### 2. Updates
```bash
# เมื่อต้องการอัปเดตแอป:
cd /path/to/your/frontend

# Update version ใน package.json
npm version patch  # หรือ minor, major

# Build ใหม่
npm run build
npx cap copy android
npx cap sync android

# Build AAB ใหม่
cd android
./gradlew bundleRelease

# อัปโหลดใน Play Console
```

### 3. Marketing
- เพิ่ม keywords ใน store listing
- ขอ reviews จากผู้ใช้
- แชร์ใน social media

---

## 🛠️ Troubleshooting

### ปัญหา: Build Failed
```bash
# ล้าง build cache
cd android
./gradlew clean

# ตรวจสอบ Android SDK
# ใน Android Studio: Tools → SDK Manager
```

### ปัญหา: Upload Failed
- ตรวจสอบว่า version code เพิ่มขึ้น
- ตรวจสอบว่า AAB file signed correctly
- ตรวจสอบ permissions ใน AndroidManifest.xml

### ปัญหา: App Rejected
- อ่าน rejection reason ใน email
- แก้ไขปัญหาตาม Google's guidelines
- Submit ใหม่

---

## 🎉 สำเร็จแล้ว!

เมื่อแอปได้รับการอนุมัติ:
1. แอปจะปรากฏใน Google Play Store
2. ผู้ใช้สามารถค้นหาและดาวน์โหลดได้
3. คุณจะได้รับ Play Store URL: `https://play.google.com/store/apps/details?id=com.yourcompany.pego`

**ขั้นตอนสุดท้าย:** แชร์ลิงก์แอปและเริ่มต้นการตลาด! 🚀