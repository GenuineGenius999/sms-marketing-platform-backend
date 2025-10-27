#!/usr/bin/env python3
"""
Database setup script for SMS Marketing Platform
This script creates the database and tables if they don't exist
"""

import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from sqlalchemy import create_engine, text
from app.core.config import settings
from app.database import engine
from app.models import Base

def create_database():
    """Create the database if it doesn't exist"""
    try:
        # Connect to PostgreSQL server (not to the specific database)
        conn = psycopg2.connect(
            host="localhost",
            port="5432",
            user="postgres",  # Default PostgreSQL superuser
            password="postgres"  # Change this to your PostgreSQL password
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = 'sms_platform'")
        exists = cursor.fetchone()
        
        if not exists:
            # Create database
            cursor.execute("CREATE DATABASE sms_platform")
            print("✅ Database 'sms_platform' created successfully")
        else:
            print("✅ Database 'sms_platform' already exists")
            
        cursor.close()
        conn.close()
        
    except psycopg2.OperationalError as e:
        print(f"❌ Error connecting to PostgreSQL: {e}")
        print("Please ensure PostgreSQL is running and accessible")
        return False
    except Exception as e:
        print(f"❌ Error creating database: {e}")
        return False
    
    return True

def create_tables():
    """Create all database tables"""
    try:
        # Test connection to the specific database
        test_engine = create_engine(
            "postgresql://sms_user:sms_password@localhost:5432/sms_platform",
            pool_pre_ping=True
        )
        
        with test_engine.connect() as conn:
            # Test the connection
            conn.execute(text("SELECT 1"))
            print("✅ Database connection successful")
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        print("This might be due to missing database or user permissions")
        return False

def create_user():
    """Create the database user if it doesn't exist"""
    try:
        # Connect as superuser
        conn = psycopg2.connect(
            host="localhost",
            port="5432",
            user="postgres",
            password="postgres"
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Check if user exists
        cursor.execute("SELECT 1 FROM pg_roles WHERE rolname = 'sms_user'")
        exists = cursor.fetchone()
        
        if not exists:
            # Create user
            cursor.execute("CREATE USER sms_user WITH PASSWORD 'sms_password'")
            cursor.execute("GRANT ALL PRIVILEGES ON DATABASE sms_platform TO sms_user")
            cursor.execute("GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO sms_user")
            cursor.execute("GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO sms_user")
            print("✅ Database user 'sms_user' created successfully")
        else:
            print("✅ Database user 'sms_user' already exists")
            
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error creating user: {e}")
        return False

def main():
    print("🚀 Setting up SMS Marketing Platform Database...")
    print("=" * 50)
    
    # Step 1: Create database
    print("📊 Creating database...")
    if not create_database():
        print("❌ Failed to create database. Please check PostgreSQL connection.")
        return False
    
    # Step 2: Create user
    print("👤 Creating database user...")
    if not create_user():
        print("❌ Failed to create user. Please check permissions.")
        return False
    
    # Step 3: Create tables
    print("📋 Creating tables...")
    if not create_tables():
        print("❌ Failed to create tables. Please check database connection.")
        return False
    
    print("=" * 50)
    print("🎉 Database setup completed successfully!")
    print("📝 You can now run the application with: python main.py")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
