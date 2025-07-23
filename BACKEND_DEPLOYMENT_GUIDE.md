# 🚀 คู่มือการ Deploy Backend Pego แบบละเอียด

## 📋 สิ่งที่คุณต้องเตรียม

### 1. **Server/VPS**
- **แนะนำ:** DigitalOcean, AWS EC2, Google Cloud, หรือ Vultr
- **Specs ขั้นต่ำ:** 2 CPU, 2GB RAM, 20GB Storage
- **OS:** Ubuntu 20.04 LTS หรือใหม่กว่า

### 2. **Domain Name**
- ซื้อ domain จาก Namecheap, GoDaddy, หรือ Cloudflare
- ตัวอย่าง: `yourdomain.com` หรือ `pego.yourdomain.com`

### 3. **SSL Certificate**
- ใช้ Let's Encrypt (ฟรี) หรือซื้อ SSL certificate

---

## 🔧 ขั้นตอนที่ 1: ติดตั้ง Docker บน Server

### เข้าสู่ Server ผ่าน SSH
```bash
ssh root@your-server-ip
```

### ติดตั้ง Docker
```bash
# อัปเดต package list
sudo apt update && sudo apt upgrade -y

# ติดตั้ง dependencies
sudo apt install -y apt-transport-https ca-certificates curl software-properties-common

# เพิ่ม Docker's official GPG key
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# เพิ่ม Docker repository
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# ติดตั้ง Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io

# เพิ่ม user ไปยัง docker group
sudo usermod -aG docker $USER

# ติดตั้ง Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# ทดสอบการติดตั้ง
docker --version
docker-compose --version
```

---

## 📦 ขั้นตอนที่ 2: อัปโหลดโค้ดไปยัง Server

### วิธีที่ 1: ใช้ Git (แนะนำ)
```bash
# ติดตั้ง Git
sudo apt install -y git

# Clone repository (ถ้าคุณมี Git repo)
git clone https://github.com/yourusername/pego-backend.git
cd pego-backend
```

### วิธีที่ 2: ใช้ SCP
```bash
# จากเครื่องคุณ, upload ไฟล์ไปยัง server
scp -r /path/to/your/backend/ root@your-server-ip:/home/pego-backend/
```

### วิธีที่ 3: สร้างโฟลเดอร์และอัปโหลดด้วยมือ
```bash
# สร้างโฟลเดอร์
mkdir -p /home/pego-backend
cd /home/pego-backend

# สร้างไฟล์ต่างๆ (copy จากไฟล์ที่เราสร้างไว้)
```

---

## ⚙️ ขั้นตอนที่ 3: กำหนดค่า Environment Variables

### สร้างไฟล์ .env.prod
```bash
cd /home/pego-backend
cp .env.prod.template .env.prod
nano .env.prod
```

### แก้ไขไฟล์ .env.prod
```bash
# Database Configuration
MONGO_ROOT_USERNAME=admin
MONGO_ROOT_PASSWORD=your-super-strong-password-here

# JWT Keys (สร้างใหม่ด้วย openssl)
JWT_SECRET_KEY=your-jwt-secret-key-64-characters-long
ADMIN_SECRET_KEY=your-admin-secret-key-64-characters-long
SESSION_SECRET_KEY=your-session-secret-key-64-characters-long

# Payment Keys
STRIPE_API_KEY=sk_live_your_stripe_key_here
PROMPTPAY_ID=0891234567

# Google OAuth
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Your Domain
FRONTEND_URL=https://yourdomain.com
```

### สร้าง Secret Keys
```bash
# สร้าง random secret keys
openssl rand -hex 32  # สำหรับ JWT_SECRET_KEY
openssl rand -hex 32  # สำหรับ ADMIN_SECRET_KEY
openssl rand -hex 32  # สำหรับ SESSION_SECRET_KEY
```

---

## 🔒 ขั้นตอนที่ 4: ตั้งค่า SSL Certificate

### วิธีที่ 1: ใช้ Let's Encrypt (ฟรี)
```bash
# ติดตั้ง Certbot
sudo apt install -y certbot

# สร้าง SSL certificate
sudo certbot certonly --standalone -d yourdomain.com

# Copy certificates
sudo mkdir -p /home/pego-backend/ssl
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem /home/pego-backend/ssl/cert.pem
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem /home/pego-backend/ssl/key.pem
sudo chown -R $USER:$USER /home/pego-backend/ssl
```

### วิธีที่ 2: ใช้ Self-signed Certificate (สำหรับทดสอบ)
```bash
mkdir -p /home/pego-backend/ssl
cd /home/pego-backend/ssl

# สร้าง self-signed certificate
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout key.pem -out cert.pem \
    -subj "/C=TH/ST=Bangkok/L=Bangkok/O=Pego/CN=yourdomain.com"
```

---

## 🌐 ขั้นตอนที่ 5: แก้ไข Nginx Configuration

```bash
cd /home/pego-backend
nano nginx.conf
```

แก้ไข `yourdomain.com` เป็น domain ของคุณ:
```nginx
server_name yourdomain.com www.yourdomain.com;
```

---

## 🚀 ขั้นตอนที่ 6: Deploy แอปพลิเคชัน

```bash
cd /home/pego-backend

# รัน deployment script
./deploy.sh
```

หรือรันแบบ manual:
```bash
# Build และ start services
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d

# ตรวจสอบ status
docker-compose -f docker-compose.prod.yml ps

# ดู logs
docker-compose -f docker-compose.prod.yml logs -f
```

---

## 🔍 ขั้นตอนที่ 7: ทดสอบการทำงาน

### ทดสอบ Backend API
```bash
# ทดสอบ API endpoint
curl http://localhost:8001/api/

# ทดสอบ admin login
curl -X POST http://localhost:8001/api/admin/login \
     -H "Content-Type: application/json" \
     -d '{"username":"admin","password":"admin123"}'
```

### ทดสอบผ่าน Domain
```bash
# ทดสอบ HTTPS
curl https://yourdomain.com/api/

# ทดสอบใน browser
# ไปที่ https://yourdomain.com/api/admin/dashboard
```

---

## 🌍 ขั้นตอนที่ 8: ตั้งค่า DNS

### ใน DNS Provider ของคุณ (Cloudflare, Namecheap, etc.)
```
Type: A
Name: @
Value: your-server-ip

Type: A  
Name: www
Value: your-server-ip

Type: A
Name: api
Value: your-server-ip
```

---

## 📊 การจัดการ Production

### ดู Logs
```bash
docker-compose -f docker-compose.prod.yml logs -f backend
docker-compose -f docker-compose.prod.yml logs -f mongodb
```

### Restart Services
```bash
docker-compose -f docker-compose.prod.yml restart backend
docker-compose -f docker-compose.prod.yml restart mongodb
```

### Backup Database
```bash
# สร้าง backup
docker-compose -f docker-compose.prod.yml exec mongodb mongodump --out /data/backup/$(date +%Y%m%d)

# Copy backup ออกมา
docker cp pego-mongodb:/data/backup ./backups/
```

### Update Code
```bash
# Pull latest code
git pull origin main

# Rebuild และ restart
docker-compose -f docker-compose.prod.yml build backend
docker-compose -f docker-compose.prod.yml up -d backend
```

---

## 🛡️ Security Best Practices

### 1. Firewall
```bash
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
```

### 2. Auto-renewal SSL
```bash
# เพิ่มใน crontab
sudo crontab -e

# เพิ่มบรรทัดนี้
0 12 * * * /usr/bin/certbot renew --quiet
```

### 3. Regular Updates
```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Update Docker images
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d
```

---

## 🆘 Troubleshooting

### ปัญหา: Container ไม่เริ่มต้น
```bash
# ดู logs
docker-compose -f docker-compose.prod.yml logs backend

# ตรวจสอบ resources
docker stats
```

### ปัญหา: Database Connection
```bash
# ทดสอบ MongoDB
docker-compose -f docker-compose.prod.yml exec mongodb mongosh

# ตรวจสอบ network
docker network ls
```

### ปัญหา: SSL Certificate
```bash
# ตรวจสอบ certificate
openssl x509 -in ssl/cert.pem -text -noout

# ต่ออายุ Let's Encrypt
sudo certbot renew
```

ขั้นตอนต่อไปคือการสร้าง Android App สำหรับ Google Play Store ครับ!