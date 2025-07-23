#!/bin/bash

# Pego Android App Builder Script
# This script automates the process of creating an Android app from your PWA

set -e

echo "📱 Pego Android App Builder"
echo "=========================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Configuration
APP_NAME="Pego"
APP_ID="com.yourcompany.pego"
APP_VERSION="1.0.0"

# Check prerequisites
print_step "Checking prerequisites..."

if ! command -v node &> /dev/null; then
    print_error "Node.js is not installed. Please install Node.js 18+ first."
    exit 1
fi

if ! command -v npx &> /dev/null; then
    print_error "NPX is not available. Please install Node.js properly."
    exit 1
fi

NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 16 ]; then
    print_error "Node.js version 16+ is required. Current version: $(node -v)"
    exit 1
fi

print_success "Node.js $(node -v) is installed"

# Check if we're in the right directory
if [ ! -f "package.json" ]; then
    print_error "package.json not found. Please run this script from your frontend directory."
    exit 1
fi

print_success "Found package.json"

# Get user configuration
echo ""
print_step "Configuration"
read -p "Enter your app name (default: Pego): " USER_APP_NAME
APP_NAME=${USER_APP_NAME:-$APP_NAME}

read -p "Enter your app ID (default: com.yourcompany.pego): " USER_APP_ID
APP_ID=${USER_APP_ID:-$APP_ID}

read -p "Enter your backend URL (https://yourdomain.com): " BACKEND_URL
if [ -z "$BACKEND_URL" ]; then
    print_error "Backend URL is required"
    exit 1
fi

# Create production environment file
print_step "Creating production environment..."
cat > .env.production << EOF
REACT_APP_BACKEND_URL=${BACKEND_URL}/api
REACT_APP_APP_NAME=${APP_NAME}
REACT_APP_VERSION=${APP_VERSION}
GENERATE_SOURCEMAP=false
EOF

print_success "Created .env.production"

# Install Capacitor if not already installed
print_step "Installing Capacitor..."
npm install @capacitor/core @capacitor/cli @capacitor/android

# Initialize Capacitor
print_step "Initializing Capacitor..."
if [ ! -f "capacitor.config.ts" ]; then
    npx cap init "$APP_NAME" "$APP_ID"
    print_success "Capacitor initialized"
else
    print_warning "Capacitor already initialized"
fi

# Update Capacitor config
print_step "Updating Capacitor configuration..."
cat > capacitor.config.ts << EOF
import { CapacitorConfig } from '@capacitor/core';

const config: CapacitorConfig = {
  appId: '${APP_ID}',
  appName: '${APP_NAME}',
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
EOF

print_success "Updated Capacitor configuration"

# Build the web app
print_step "Building web app for production..."
npm run build

if [ ! -d "build" ]; then
    print_error "Build failed. No build directory found."
    exit 1
fi

print_success "Web app built successfully"

# Add Android platform
print_step "Adding Android platform..."
if [ ! -d "android" ]; then
    npx cap add android
    print_success "Android platform added"
else
    print_warning "Android platform already exists"
fi

# Sync web assets
print_step "Syncing web assets..."
npx cap copy android
npx cap sync android

print_success "Assets synced"

# Update Android configuration
print_step "Updating Android configuration..."

# Update build.gradle
cat > android/app/build.gradle.template << 'EOF'
apply plugin: 'com.android.application'

android {
    compileSdkVersion rootProject.ext.compileSdkVersion
    defaultConfig {
        applicationId "APP_ID_PLACEHOLDER"
        minSdkVersion rootProject.ext.minSdkVersion
        targetSdkVersion rootProject.ext.targetSdkVersion
        versionCode 1
        versionName "1.0.0"
        testInstrumentationRunner "androidx.test.runner.AndroidJUnitRunner"
        aaptOptions {
             // Files and dirs to omit from the packaged APK/AAB
             // Ref: https://android.googlesource.com/platform/frameworks/base/+/282e181b58cf72b6ca770dc7ca5f91f135444502/tools/aapt/AaptAssets.cpp#61
            ignoreAssetsPattern '!.svn:!.git:!.ds_store:!*.scc:.*:!CVS:!thumbs.db:!picasa.ini:!*~'
        }
    }
    buildTypes {
        release {
            minifyEnabled false
            proguardFiles getDefaultProguardFile('proguard-android.txt'), 'proguard-rules.pro'
        }
    }
}

repositories {
    flatDir{
        dirs '../capacitor-cordova-android-plugins/src/main/libs', 'libs'
    }
}

dependencies {
    implementation fileTree(dir: 'libs', include: ['*.jar'])
    implementation "androidx.appcompat:appcompat:$androidxAppCompatVersion"
    implementation project(':capacitor-android')
    testImplementation "junit:junit:$junitVersion"
    androidTestImplementation "androidx.test.ext:junit:$androidxJunitVersion"
    androidTestImplementation "androidx.test.espresso:espresso-core:$androidxEspressoCoreVersion"
    implementation project(':capacitor-cordova-android-plugins')
}

apply from: 'capacitor.build.gradle'

try {
    def servicesJSON = file('google-services.json')
    if (servicesJSON.text) {
        apply plugin: 'com.google.gms.google-services'
    }
} catch(Exception e) {
    logger.info("google-services.json not found, google-services plugin not applied. Push Notifications won't work")
}
EOF

# Replace APP_ID placeholder
sed "s/APP_ID_PLACEHOLDER/$APP_ID/g" android/app/build.gradle.template > android/app/build.gradle
rm android/app/build.gradle.template

# Update AndroidManifest.xml
MANIFEST_FILE="android/app/src/main/AndroidManifest.xml"
if [ -f "$MANIFEST_FILE" ]; then
    # Add permissions if not already present
    if ! grep -q "android.permission.CAMERA" "$MANIFEST_FILE"; then
        sed -i '/<\/manifest>/i\    <uses-permission android:name="android.permission.CAMERA" />' "$MANIFEST_FILE"
    fi
    if ! grep -q "android.permission.RECORD_AUDIO" "$MANIFEST_FILE"; then
        sed -i '/<\/manifest>/i\    <uses-permission android:name="android.permission.RECORD_AUDIO" />' "$MANIFEST_FILE"
    fi
    if ! grep -q "android.permission.READ_EXTERNAL_STORAGE" "$MANIFEST_FILE"; then
        sed -i '/<\/manifest>/i\    <uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE" />' "$MANIFEST_FILE"
    fi
fi

print_success "Android configuration updated"

# Create keystore for signing (if not exists)
print_step "Setting up app signing..."
KEYSTORE_FILE="pego-release-key.keystore"

if [ ! -f "$KEYSTORE_FILE" ]; then
    print_warning "Keystore not found. You'll need to create one for Play Store release."
    echo "To create a keystore, run:"
    echo "keytool -genkey -v -keystore $KEYSTORE_FILE -keyalg RSA -keysize 2048 -validity 10000 -alias pego"
    echo ""
    echo "Then create android/keystore.properties with:"
    echo "storeFile=../$KEYSTORE_FILE"
    echo "storePassword=your-keystore-password"
    echo "keyAlias=pego"
    echo "keyPassword=your-key-password"
else
    print_success "Keystore found: $KEYSTORE_FILE"
fi

# Generate app icons (basic template)
print_step "Setting up app icons..."
ICON_DIR="android/app/src/main/res"
if [ ! -f "$ICON_DIR/mipmap-hdpi/ic_launcher.png" ]; then
    print_warning "Custom app icons not found. Using default Capacitor icons."
    print_warning "For custom icons, replace files in: $ICON_DIR/mipmap-*/ic_launcher.png"
fi

# Create build scripts
print_step "Creating build scripts..."

cat > build-android.sh << 'EOF'
#!/bin/bash
echo "Building Android App..."

# Build web assets
npm run build

# Sync with Capacitor
npx cap copy android
npx cap sync android

# Build debug APK
echo "Building debug APK..."
cd android
./gradlew assembleDebug

echo "Debug APK built: android/app/build/outputs/apk/debug/app-debug.apk"

# Build unsigned release AAB (if keystore is configured)
if [ -f "keystore.properties" ]; then
    echo "Building release AAB..."
    ./gradlew bundleRelease
    echo "Release AAB built: android/app/build/outputs/bundle/release/app-release.aab"
else
    echo "No keystore configured. Skipping release build."
    echo "Configure keystore.properties to build release version."
fi

cd ..
echo "Build complete!"
EOF

chmod +x build-android.sh

cat > open-android.sh << 'EOF'
#!/bin/bash
echo "Opening Android project in Android Studio..."
npx cap open android
EOF

chmod +x open-android.sh

print_success "Build scripts created"

# Final instructions
echo ""
print_success "🎉 Android app setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Install Android Studio if you haven't: https://developer.android.com/studio"
echo "2. Create a keystore for app signing (see instructions above)"
echo "3. Run: ./open-android.sh to open the project in Android Studio"
echo "4. Or run: ./build-android.sh to build the app"
echo ""
echo "📱 Files created:"
echo "  - capacitor.config.ts (Capacitor configuration)"
echo "  - .env.production (Production environment)"
echo "  - build-android.sh (Build script)"
echo "  - open-android.sh (Open in Android Studio)"
echo "  - android/ (Android project)"
echo ""
echo "🔧 For Play Store release:"
echo "  1. Create and configure keystore"
echo "  2. Build release AAB: cd android && ./gradlew bundleRelease"
echo "  3. Upload AAB to Google Play Console"
echo ""
print_success "Ready to build your Android app! 🚀"