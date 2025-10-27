#!/usr/bin/env python3
"""
Database Update Script
This script will update the database schema to add the new columns for two-way SMS support.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from app.core.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_database():
    """Update the database schema"""
    try:
        # Create engine
        engine = create_engine(settings.DATABASE_URL)
        
        with engine.connect() as conn:
            # Check if contact_id column exists
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'messages' AND column_name = 'contact_id'
            """))
            
            if not result.fetchone():
                logger.info("Adding contact_id column to messages table...")
                conn.execute(text("ALTER TABLE messages ADD COLUMN contact_id INTEGER"))
                conn.execute(text("ALTER TABLE messages ADD CONSTRAINT fk_messages_contact_id FOREIGN KEY (contact_id) REFERENCES contacts(id)"))
                conn.commit()
                logger.info("✅ contact_id column added successfully")
            else:
                logger.info("✅ contact_id column already exists")
            
            # Check if message_id column exists
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'messages' AND column_name = 'message_id'
            """))
            
            if not result.fetchone():
                logger.info("Adding message_id column to messages table...")
                conn.execute(text("ALTER TABLE messages ADD COLUMN message_id VARCHAR"))
                conn.commit()
                logger.info("✅ message_id column added successfully")
            else:
                logger.info("✅ message_id column already exists")
            
            # Check if is_incoming column exists
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'messages' AND column_name = 'is_incoming'
            """))
            
            if not result.fetchone():
                logger.info("Adding is_incoming column to messages table...")
                conn.execute(text("ALTER TABLE messages ADD COLUMN is_incoming VARCHAR DEFAULT 'false'"))
                conn.commit()
                logger.info("✅ is_incoming column added successfully")
            else:
                logger.info("✅ is_incoming column already exists")
            
            # Update campaign_id to be nullable
            logger.info("Updating campaign_id to be nullable...")
            conn.execute(text("ALTER TABLE messages ALTER COLUMN campaign_id DROP NOT NULL"))
            conn.commit()
            logger.info("✅ campaign_id updated to be nullable")
            
            logger.info("🎉 Database update completed successfully!")
            
    except Exception as e:
        logger.error(f"❌ Database update failed: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    success = update_database()
    if success:
        print("✅ Database updated successfully!")
    else:
        print("❌ Database update failed!")
        sys.exit(1)
