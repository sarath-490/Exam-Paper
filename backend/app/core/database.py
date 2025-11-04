from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorGridFSBucket
from app.core.config import settings
from typing import Optional

class Database:
    client: Optional[AsyncIOMotorClient] = None
    db = None
    fs: Optional[AsyncIOMotorGridFSBucket] = None

db = Database()


async def connect_to_mongo():
    """Connect to MongoDB Atlas"""
    try:
        # Connect to MongoDB Atlas
        db.client = AsyncIOMotorClient(
            settings.MONGODB_URI,
            serverSelectionTimeoutMS=5000,
            maxPoolSize=50
        )
        
        # Use the specified database name
        db.db = db.client[settings.MONGODB_DB_NAME]
        
        # GridFS for backward compatibility (though we'll use Cloudinary for new uploads)
        db.fs = AsyncIOMotorGridFSBucket(db.db)
        
        # Test connection
        await db.client.admin.command('ping')
        
        print(f"✅ Connected to MongoDB Atlas: {settings.MONGODB_DB_NAME}")
        
        # Create indexes for better performance
        await create_indexes()
        
    except Exception as e:
        print(f"❌ Failed to connect to MongoDB Atlas: {e}")
        raise


async def create_indexes():
    """Create database indexes for better query performance"""
    try:
        # Users collection indexes
        await db.db.users.create_index("email", unique=True)
        await db.db.users.create_index("role")
        
        # Resources collection indexes
        await db.db.resources.create_index("teacher_id")
        await db.db.resources.create_index("subject")
        await db.db.resources.create_index([("subject", 1), ("teacher_id", 1)])
        
        # Papers collection indexes
        await db.db.papers.create_index("teacher_id")
        await db.db.papers.create_index("status")
        await db.db.papers.create_index([("teacher_id", 1), ("status", 1)])
        await db.db.papers.create_index([("subject", 1), ("status", 1)])
        
        # History collection indexes
        await db.db.prompts_history.create_index("teacher_id")
        await db.db.prompts_history.create_index("created_at")
        
        print("✅ Database indexes created")
        
    except Exception as e:
        print(f"⚠️ Error creating indexes: {e}")


async def close_mongo_connection():
    """Close MongoDB connection"""
    if db.client:
        db.client.close()
        print("❌ Closed MongoDB connection")


def get_database():
    """Get database instance"""
    return db.db


def get_gridfs():
    """Get GridFS instance for file storage (legacy support)"""
    return db.fs
