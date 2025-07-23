@echo off
chcp 65001 >nul
color 0A
echo.
echo ========================================
echo    🚀 Pego App - Easy Store Deployment
echo ========================================
echo.

echo [ขั้นตอน 1/8] 📥 กำลังดาวน์โหลดโค้ดจาก Github...
git clone https://github.com/successnhoom/Pego.git pego-app
if errorlevel 1 (
    echo ❌ ไม่สามารถดาวน์โหลดจาก Github ได้
    echo กรุณาตรวจสอบว่าติดตั้ง Git แล้วหรือไม่
    pause
    exit /b 1
)

cd pego-app
echo ✅ ดาวน์โหลดสำเร็จ!
echo.

echo [ขั้นตอน 2/8] 📦 กำลังติดตั้ง Node.js dependencies...
cd frontend
call npm install
if errorlevel 1 (
    echo ❌ ไม่สามารถติดตั้ง Node.js packages ได้
    echo กรุณาตรวจสอบว่าติดตั้ง Node.js แล้วหรือไม่
    pause
    exit /b 1
)
echo ✅ ติดตั้ง Node.js packages สำเร็จ!
echo.

echo [ขั้นตอน 3/8] ⚡ กำลังติดตั้ง Capacitor (แปลงเว็บเป็นแอป)...
call npm install @capacitor/core @capacitor/cli @capacitor/android
if errorlevel 1 (
    echo ❌ ไม่สามารถติดตั้ง Capacitor ได้
    pause
    exit /b 1
)
echo ✅ ติดตั้ง Capacitor สำเร็จ!
echo.

echo [ขั้นตอน 4/8] 🔧 กำลังตั้งค่า Capacitor...
call npx cap init "Pego" "com.pego.videocontest"
echo ✅ ตั้งค่า Capacitor สำเร็จ!
echo.

echo [ขั้นตอน 5/8] 🏗️ กำลัง Build โปรเจคสำหรับ Production...
call npm run build
if errorlevel 1 (
    echo ❌ Build ไม่สำเร็จ
    pause
    exit /b 1
)
echo ✅ Build สำเร็จ!
echo.

echo [ขั้นตอน 6/8] 🤖 กำลังเพิ่ม Android Platform...
call npx cap add android
if errorlevel 1 (
    echo ❌ เพิ่ม Android Platform ไม่สำเร็จ
    pause
    exit /b 1
)
echo ✅ เพิ่ม Android Platform สำเร็จ!
echo.

echo [ขั้นตอน 7/8] 🔄 กำลัง Sync ไฟล์...
call npx cap sync android
echo ✅ Sync ไฟล์สำเร็จ!
echo.

echo [ขั้นตอน 8/8] 📱 กำลังเปิด Android Studio...
echo.
echo ========================================
echo           🎉 เตรียมการเสร็จสิ้น!
echo ========================================
echo.
echo ✅ โปรเจค Pego พร้อมขึ้น Google Play Store แล้ว!
echo.
echo 📋 ขั้นตอนถัดไป:
echo    1. Android Studio จะเปิดขึ้นมา
echo    2. รอให้ Gradle sync เสร็จ (5-10 นาที)
echo    3. กด Build → Generate Signed Bundle / APK
echo    4. เลือก Android App Bundle (.aab)
echo    5. นำไฟล์ .aab ไปอัพโหลด Google Play Console
echo.
echo 💰 ค่าใช้จ่าย: Google Play Console = $25 (ครั้งเดียว)
echo ⏰ เวลารอตรวจสอบ: 1-7 วัน
echo.
echo กด Enter เพื่อเปิด Android Studio...
pause

call npx cap open android

echo.
echo ========================================
echo      🎯 ขั้นตอนถัดไป - Google Play Store
echo ========================================
echo.
echo 1. สมัครบัญชี: https://play.google.com/console
echo 2. จ่ายค่าสมัคร: $25
echo 3. สร้างแอปใหม่ชื่อ: "Pego - แข่งขันวิดีโอสั้น"
echo 4. อัพโหลดไฟล์ .aab ที่ได้จาก Android Studio
echo 5. กรอกข้อมูลแอป (ชื่อ, คำอธิบาย, รูปภาพ)
echo 6. ส่งเพื่อตรวจสอบ
echo.
echo 📧 ผลการตรวจสอบจะส่งทางอีเมลใน 1-7 วัน
echo.
echo 🎊 ขอให้โชคดีกับแอป Pego ของคุณ!
echo.
pause