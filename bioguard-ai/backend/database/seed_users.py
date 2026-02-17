"""Seed demo users for BioGuard AI login system."""
from sqlalchemy.orm import Session
from database.db import SessionLocal
from database.models import User
from auth.auth import get_password_hash
from loguru import logger


def seed_demo_users():
    """Create demo user accounts if they don't exist."""
    db = SessionLocal()
    
    try:
        demo_users = [
            # ANALYZER ACCOUNTS
            {
                "username": "dr_sharma",
                "email": "dr.sharma@bioguard.ai",
                "password": "BioGuard@2026",
                "role": "analyzer",
                "device_id": None,
                "village_id": None,
                "village_name": None
            },
            {
                "username": "district_mh",
                "email": "district.mh@bioguard.ai",
                "password": "Maharashtra#1",
                "role": "analyzer",
                "device_id": None,
                "village_id": None,
                "village_name": None
            },
            {
                "username": "admin",
                "email": "admin@bioguard.ai",
                "password": "Admin@BioGuard",
                "role": "analyzer",
                "device_id": None,
                "village_id": None,
                "village_name": None
            },
            # PI SENDER ACCOUNTS
            {
                "username": "rpi5_shirpur",
                "email": "rpi5.shirpur@bioguard.ai",
                "password": "Pi@Shirpur001",
                "role": "pi_sender",
                "device_id": "RPI5-UNIT-001",
                "village_id": "MH_SHP",
                "village_name": "Shirpur"
            },
            {
                "username": "rpi5_dharangaon",
                "email": "rpi5.dharangaon@bioguard.ai",
                "password": "Pi@Dharangaon002",
                "role": "pi_sender",
                "device_id": "RPI5-UNIT-002",
                "village_id": "MH_DHA",
                "village_name": "Dharangaon"
            },
            {
                "username": "rpi5_bahraich",
                "email": "rpi5.bahraich@bioguard.ai",
                "password": "Pi@Bahraich003",
                "role": "pi_sender",
                "device_id": "RPI5-UNIT-003",
                "village_id": "UP_BAH",
                "village_name": "Bahraich"
            }
        ]
        
        users_created = 0
        
        for user_data in demo_users:
            # Check if user already exists
            existing_user = db.query(User).filter(User.username == user_data["username"]).first()
            
            if not existing_user:
                # Create new user
                new_user = User(
                    username=user_data["username"],
                    email=user_data["email"],
                    hashed_password=get_password_hash(user_data["password"]),
                    role=user_data["role"],
                    device_id=user_data["device_id"],
                    village_id=user_data["village_id"],
                    village_name=user_data["village_name"],
                    is_active=True
                )
                db.add(new_user)
                users_created += 1
                logger.info(f"✅ Created demo user: {user_data['username']} ({user_data['role']})")
        
        db.commit()
        
        if users_created > 0:
            logger.info(f"🎭 Seeded {users_created} demo user accounts")
        else:
            logger.info("ℹ️  Demo users already exist")
            
    except Exception as e:
        logger.error(f"❌ Error seeding demo users: {e}")
        db.rollback()
    finally:
        db.close()
