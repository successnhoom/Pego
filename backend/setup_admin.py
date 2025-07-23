#!/usr/bin/env python3
"""
Simple script to create admin user without interaction
"""

import asyncio
import os
import sys
from pathlib import Path
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent))

from models import AdminUser
import bcrypt

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
db_name = os.environ.get('DB_NAME', 'pego_database')

def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

async def create_default_admin():
    """Create default admin user"""
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    try:
        print("🔧 Creating default admin user...")
        
        # Check if admin users exist
        existing_admin = await db.admin_users.find_one({})
        if existing_admin:
            print("✅ Admin users already exist!")
            return
            
        # Create default admin
        admin_user = AdminUser(
            username="admin",
            email="admin@pego.com",
            password_hash=hash_password("admin123"),
            role="super_admin",
            permissions=["full_access"]
        )
        
        await db.admin_users.insert_one(admin_user.dict())
        
        print("🎉 Default admin user created successfully!")
        print("   Username: admin")
        print("   Password: admin123")
        print("   Role: super_admin")
        print("")
        print("   ⚠️  Please change the password after first login!")
        print("   Access admin panel at: http://localhost:3000/admin")
        
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(create_default_admin())