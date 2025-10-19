"""
User service for managing users in MongoDB.
"""
from datetime import datetime
from typing import Optional
from pymongo import MongoClient
from logzero import logger
import os
from dotenv import load_dotenv

from app.auth import get_password_hash, verify_password, User, UserCreate

load_dotenv()

# MongoDB connection
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
mongo_client = MongoClient(MONGO_URI)
db = mongo_client["trading_data"]
users_collection = db["users"]

# Create unique index on email
users_collection.create_index("email", unique=True)

def create_user(user_data: UserCreate) -> Optional[User]:
    """
    Create a new user in MongoDB.
    
    Args:
        user_data: User registration data
        
    Returns:
        User object if successful, None otherwise
    """
    try:
        # Check if user already exists
        existing_user = users_collection.find_one({"email": user_data.email})
        if existing_user:
            logger.warning(f"User with email {user_data.email} already exists")
            return None
        
        # Hash password
        hashed_password = get_password_hash(user_data.password)
        
        # Create user document
        user_doc = {
            "email": user_data.email,
            "full_name": user_data.full_name,
            "hashed_password": hashed_password,
            "is_active": True,
            "created_at": datetime.utcnow(),
            "last_login": None
        }
        
        # Insert into MongoDB
        result = users_collection.insert_one(user_doc)
        
        if result.inserted_id:
            logger.info(f"User created successfully: {user_data.email}")
            return User(
                email=user_data.email,
                full_name=user_data.full_name,
                is_active=True,
                created_at=user_doc["created_at"]
            )
        
        return None
        
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        return None

def get_user_by_email(email: str) -> Optional[User]:
    """
    Get user by email from MongoDB.
    
    Args:
        email: User email
        
    Returns:
        User object if found, None otherwise
    """
    try:
        user_doc = users_collection.find_one({"email": email})
        if not user_doc:
            return None
        
        return User(
            email=user_doc["email"],
            full_name=user_doc["full_name"],
            is_active=user_doc.get("is_active", True),
            created_at=user_doc["created_at"],
            last_login=user_doc.get("last_login")
        )
        
    except Exception as e:
        logger.error(f"Error getting user: {e}")
        return None

def authenticate_user(email: str, password: str) -> Optional[User]:
    """
    Authenticate a user with email and password.
    
    Args:
        email: User email
        password: Plain text password
        
    Returns:
        User object if authentication successful, None otherwise
    """
    try:
        user_doc = users_collection.find_one({"email": email})
        if not user_doc:
            logger.warning(f"User not found: {email}")
            return None
        
        if not verify_password(password, user_doc["hashed_password"]):
            logger.warning(f"Invalid password for user: {email}")
            return None
        
        # Update last login
        users_collection.update_one(
            {"email": email},
            {"$set": {"last_login": datetime.utcnow()}}
        )
        
        return User(
            email=user_doc["email"],
            full_name=user_doc["full_name"],
            is_active=user_doc.get("is_active", True),
            created_at=user_doc["created_at"],
            last_login=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Error authenticating user: {e}")
        return None

def update_user_last_login(email: str):
    """Update user's last login timestamp."""
    try:
        users_collection.update_one(
            {"email": email},
            {"$set": {"last_login": datetime.utcnow()}}
        )
    except Exception as e:
        logger.error(f"Error updating last login: {e}")

def get_all_users() -> list:
    """Get all users (admin function)."""
    try:
        users = []
        for user_doc in users_collection.find():
            users.append(User(
                email=user_doc["email"],
                full_name=user_doc["full_name"],
                is_active=user_doc.get("is_active", True),
                created_at=user_doc["created_at"],
                last_login=user_doc.get("last_login")
            ))
        return users
    except Exception as e:
        logger.error(f"Error getting all users: {e}")
        return []

def create_default_admin_user():
    """Create a default admin user if no users exist."""
    try:
        count = users_collection.count_documents({})
        if count == 0:
            logger.info("No users found. Creating default admin user...")
            admin_user = UserCreate(
                email="admin@finns.com",
                password="admin123",
                full_name="Admin User"
            )
            user = create_user(admin_user)
            if user:
                logger.info("✅ Default admin user created: admin@finns.com / admin123")
                logger.warning("⚠️ PLEASE CHANGE THE DEFAULT PASSWORD IMMEDIATELY!")
            else:
                logger.error("❌ Failed to create default admin user")
    except Exception as e:
        logger.error(f"Error creating default admin user: {e}")

