#!/usr/bin/env python3
"""
Sample data seeder for SMS Marketing Platform
Run this script to populate the database with sample data
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app.models import Base, User, Contact, ContactGroup, SmsTemplate, Campaign, SenderId
from app.core.security import get_password_hash
from datetime import datetime, timedelta
import random

# Create all tables
Base.metadata.create_all(bind=engine)

def create_sample_data():
    db = SessionLocal()
    
    try:
        # Create admin user
        admin_user = User(
            email="admin@example.com",
            name="Admin User",
            hashed_password=get_password_hash("admin123"),
            role="admin",
            is_active=True,
            balance=1000.0,
            company="SMS Platform Inc",
            phone="+1234567890"
        )
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        print("✅ Created admin user: admin@example.com / admin123")
        
        # Create sample client users
        clients = [
            {
                "email": "client1@example.com",
                "name": "John Smith",
                "company": "Tech Solutions Inc",
                "phone": "+1234567891",
                "balance": 500.0
            },
            {
                "email": "client2@example.com", 
                "name": "Sarah Johnson",
                "company": "Marketing Pro",
                "phone": "+1234567892",
                "balance": 750.0
            },
            {
                "email": "client3@example.com",
                "name": "Mike Wilson",
                "company": "Retail Plus",
                "phone": "+1234567893",
                "balance": 300.0
            }
        ]
        
        created_clients = []
        for client_data in clients:
            client = User(
                email=client_data["email"],
                name=client_data["name"],
                hashed_password=get_password_hash("password123"),
                role="client",
                is_active=True,
                balance=client_data["balance"],
                company=client_data["company"],
                phone=client_data["phone"]
            )
            db.add(client)
            db.commit()
            db.refresh(client)
            created_clients.append(client)
            print(f"✅ Created client: {client_data['email']} / password123")
        
        # Create contact groups for each client
        for client in created_clients:
            groups = [
                {"name": "VIP Customers", "description": "High-value customers"},
                {"name": "Newsletter Subscribers", "description": "Email newsletter subscribers"},
                {"name": "Recent Purchases", "description": "Customers who bought in last 30 days"},
                {"name": "Inactive Users", "description": "Customers who haven't engaged recently"}
            ]
            
            for group_data in groups:
                group = ContactGroup(
                    name=group_data["name"],
                    description=group_data["description"],
                    user_id=client.id
                )
                db.add(group)
                db.commit()
                db.refresh(group)
                print(f"✅ Created group '{group_data['name']}' for {client.email}")
        
        # Create sample contacts for each client
        sample_contacts = [
            {"name": "Alice Brown", "phone": "+1234567001", "email": "alice@example.com"},
            {"name": "Bob Davis", "phone": "+1234567002", "email": "bob@example.com"},
            {"name": "Carol White", "phone": "+1234567003", "email": "carol@example.com"},
            {"name": "David Lee", "phone": "+1234567004", "email": "david@example.com"},
            {"name": "Emma Taylor", "phone": "+1234567005", "email": "emma@example.com"},
            {"name": "Frank Miller", "phone": "+1234567006", "email": "frank@example.com"},
            {"name": "Grace Wilson", "phone": "+1234567007", "email": "grace@example.com"},
            {"name": "Henry Moore", "phone": "+1234567008", "email": "henry@example.com"},
            {"name": "Ivy Chen", "phone": "+1234567009", "email": "ivy@example.com"},
            {"name": "Jack Anderson", "phone": "+1234567010", "email": "jack@example.com"}
        ]
        
        for client in created_clients:
            # Get client's groups
            client_groups = db.query(ContactGroup).filter(ContactGroup.user_id == client.id).all()
            
            for i, contact_data in enumerate(sample_contacts):
                contact = Contact(
                    name=contact_data["name"],
                    phone=contact_data["phone"],
                    email=contact_data["email"],
                    user_id=client.id,
                    group_id=random.choice(client_groups).id if client_groups else None
                )
                db.add(contact)
                print(f"✅ Created contact '{contact_data['name']}' for {client.email}")
        
        db.commit()
        
        # Create SMS templates for each client
        templates = [
            {
                "name": "Welcome Message",
                "content": "Welcome to our service! We're excited to have you on board. Reply STOP to opt out."
            },
            {
                "name": "Promotional Offer",
                "content": "🎉 Special offer just for you! Get 20% off your next purchase. Use code SAVE20. Valid until end of month."
            },
            {
                "name": "Order Confirmation",
                "content": "Your order #ORDER123 has been confirmed. Expected delivery: 2-3 business days. Track at: [link]"
            },
            {
                "name": "Appointment Reminder",
                "content": "Reminder: You have an appointment tomorrow at 2:00 PM. Reply CONFIRM to confirm or RESCHEDULE to reschedule."
            },
            {
                "name": "Payment Due",
                "content": "Your payment of $AMOUNT is due on DATE. Please pay online at [link] or call us at [phone]."
            }
        ]
        
        for client in created_clients:
            for template_data in templates:
                template = SmsTemplate(
                    name=template_data["name"],
                    content=template_data["content"],
                    user_id=client.id,
                    is_approved=random.choice([True, True, True, False])  # 75% approved
                )
                db.add(template)
                print(f"✅ Created template '{template_data['name']}' for {client.email}")
        
        db.commit()
        
        # Create sample campaigns
        campaign_templates = [
            {
                "name": "Holiday Sale Campaign",
                "message": "🎄 Holiday Sale! Get 30% off everything. Shop now at [link]. Happy holidays!",
                "status": "sent"
            },
            {
                "name": "New Product Launch",
                "message": "🚀 Introducing our new product! Be the first to try it. Pre-order now at [link].",
                "status": "scheduled"
            },
            {
                "name": "Customer Feedback",
                "message": "Hi! How was your recent experience with us? We'd love your feedback: [link]",
                "status": "draft"
            }
        ]
        
        for client in created_clients:
            for i, campaign_data in enumerate(campaign_templates):
                campaign = Campaign(
                    name=campaign_data["name"],
                    message=campaign_data["message"],
                    user_id=client.id,
                    status=campaign_data["status"],
                    total_recipients=random.randint(50, 200),
                    delivered_count=random.randint(40, 180) if campaign_data["status"] == "sent" else 0,
                    failed_count=random.randint(0, 10) if campaign_data["status"] == "sent" else 0,
                    sent_at=datetime.utcnow() - timedelta(days=random.randint(1, 30)) if campaign_data["status"] == "sent" else None,
                    scheduled_at=datetime.utcnow() + timedelta(days=random.randint(1, 7)) if campaign_data["status"] == "scheduled" else None
                )
                db.add(campaign)
                print(f"✅ Created campaign '{campaign_data['name']}' for {client.email}")
        
        db.commit()
        
        # Create sender IDs
        sender_ids = [
            {"sender_id": "SMSAPP", "is_approved": True},
            {"sender_id": "TECHSOL", "is_approved": True},
            {"sender_id": "MARKET", "is_approved": False},
            {"sender_id": "RETAIL", "is_approved": True}
        ]
        
        for sender_data in sender_ids:
            sender = SenderId(
                sender_id=sender_data["sender_id"],
                user_id=admin_user.id,
                is_approved=sender_data["is_approved"]
            )
            db.add(sender)
            print(f"✅ Created sender ID '{sender_data['sender_id']}' - {'Approved' if sender_data['is_approved'] else 'Pending'}")
        
        db.commit()
        
        print("\n🎉 Sample data created successfully!")
        print("\n📋 Summary:")
        print(f"   👤 Users: 1 admin + {len(created_clients)} clients")
        print(f"   📞 Contacts: {len(sample_contacts) * len(created_clients)} total")
        print(f"   📁 Groups: {len(groups) * len(created_clients)} total")
        print(f"   📝 Templates: {len(templates) * len(created_clients)} total")
        print(f"   📢 Campaigns: {len(campaign_templates) * len(created_clients)} total")
        print(f"   🆔 Sender IDs: {len(sender_ids)} total")
        
        print("\n🔑 Login Credentials:")
        print("   Admin: admin@example.com / admin123")
        for client in created_clients:
            print(f"   Client: {client.email} / password123")
        
    except Exception as e:
        print(f"❌ Error creating sample data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_sample_data()
