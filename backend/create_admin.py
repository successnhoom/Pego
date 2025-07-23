#!/usr/bin/env python3
"""
Script to create the first admin user for Pego Admin Dashboard
Run this script to create an admin account before using the admin panel
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

async def create_admin_user():
    """Create admin user interactively"""
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    try:
        print("🔧 Pego Admin User Creation")
        print("=" * 40)
        
        # Check if any admin users exist
        existing_admin = await db.admin_users.find_one({})
        if existing_admin:
            print("⚠️  Admin users already exist!")
            overwrite = input("Do you want to create another admin user? (y/N): ").lower()
            if overwrite != 'y':
                print("Cancelled.")
                return
        
        # Get admin details
        print("\n📝 Enter admin details:")
        username = input("Username: ").strip()
        if not username:
            print("❌ Username cannot be empty!")
            return
            
        # Check if username exists
        existing = await db.admin_users.find_one({"username": username})
        if existing:
            print(f"❌ Username '{username}' already exists!")
            return
        
        email = input("Email: ").strip()
        if not email:
            print("❌ Email cannot be empty!")
            return
            
        # Check if email exists
        existing_email = await db.admin_users.find_one({"email": email})
        if existing_email:
            print(f"❌ Email '{email}' already exists!")
            return
        
        password = input("Password: ").strip()
        if not password or len(password) < 6:
            print("❌ Password must be at least 6 characters!")
            return
            
        # Role selection
        print("\n👤 Select role:")
        print("1. super_admin (Full access)")
        print("2. admin (Standard admin)")
        print("3. moderator (Limited access)")
        
        role_choice = input("Choose (1-3): ").strip()
        role_map = {"1": "super_admin", "2": "admin", "3": "moderator"}
        role = role_map.get(role_choice, "admin")
        
        # Confirm details
        print(f"\n✅ Creating admin user:")
        print(f"   Username: {username}")
        print(f"   Email: {email}")
        print(f"   Role: {role}")
        
        confirm = input("\nProceed? (Y/n): ").lower()
        if confirm == 'n':
            print("Cancelled.")
            return
        
        # Create admin user
        admin_user = AdminUser(
            username=username,
            email=email,
            password_hash=hash_password(password),
            role=role,
            permissions=["full_access"] if role == "super_admin" else ["moderate_content"]
        )
        
        await db.admin_users.insert_one(admin_user.dict())
        
        print("\n🎉 Admin user created successfully!")
        print(f"   Admin ID: {admin_user.id}")
        print(f"   You can now login to the admin panel with:")
        print(f"   Username: {username}")
        print(f"   Password: [your password]")
        
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        
    finally:
        client.close()

if __name__ == "__main__":
    print("🚀 Starting admin user creation...")
    asyncio.run(create_admin_user())