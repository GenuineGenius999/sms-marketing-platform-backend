#!/usr/bin/env python3
"""
Script to create admin and client users in the database
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models.user import User
from app.core.security import get_password_hash
from sqlalchemy import text

def create_users():
    db = SessionLocal()
    try:
        # Check if admin user exists
        admin_user = db.query(User).filter(User.email == "admin@example.com").first()
        
        if not admin_user:
            print("Creating admin user...")
            admin_user = User(
                email="admin@example.com",
                name="Admin User",
                hashed_password=get_password_hash("admin123"),
                role="admin",
                is_active=True,
                balance=1000.0,
                company="SMS Platform Admin",
                phone="+1234567890"
            )
            db.add(admin_user)
            print("✅ Admin user created")
        else:
            print("✅ Admin user already exists")
        
        # Check if client user exists
        client_user = db.query(User).filter(User.email == "client@example.com").first()
        
        if not client_user:
            print("Creating client user...")
            client_user = User(
                email="client@example.com",
                name="Client User",
                hashed_password=get_password_hash("client123"),
                role="client",
                is_active=True,
                balance=100.0,
                company="Test Company",
                phone="+1234567891"
            )
            db.add(client_user)
            print("✅ Client user created")
        else:
            print("✅ Client user already exists")
        
        db.commit()
        
        # Verify users
        print("\n📊 User Verification:")
        users = db.query(User).all()
        for user in users:
            print(f"  - {user.email} ({user.role}) - Active: {user.is_active}")
        
        print(f"\n🎉 Total users in database: {len(users)}")
        
    except Exception as e:
        print(f"❌ Error creating users: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("🔧 Setting up SMS Marketing Platform users...")
    create_users()
    print("✅ User setup complete!")
