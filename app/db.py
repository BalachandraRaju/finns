"""
Database configuration for Finns Trading System.
Uses MongoDB for all data storage and Redis for caching.
"""
import os
import redis
from dotenv import load_dotenv

load_dotenv()

print("📊 Using MongoDB for all data storage")

# --- Redis Cache Setup ---
redis_client = None
try:
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    redis_client = redis.from_url(redis_url, decode_responses=True)
    redis_client.ping()
    print("✅ Connected to Redis successfully!")
except redis.exceptions.ConnectionError as e:
    print(f"⚠️  Could not connect to Redis: {e}")
    print("WARNING: Redis not connected. The application will use in-memory storage, and data will be lost on restart.")
    redis_client = None