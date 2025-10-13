"""
UBO Trace Engine Backend - Database Configuration
"""

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class Database:
    client: Optional[AsyncIOMotorClient] = None
    database: Optional[AsyncIOMotorDatabase] = None

# Global database instance
db = Database()

async def connect_to_mongo():
    """Create database connection"""
    try:
        from utils.settings import settings
        
        db.client = AsyncIOMotorClient(settings.mongodb_url)
        db.database = db.client[settings.database_name]
        
        # Test the connection
        await db.client.admin.command('ping')
        logger.info(f"Connected to MongoDB: {settings.database_name}")
        
        # Create indexes for better performance
        await create_indexes()
        
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise Exception(f"Database connection failed: {e}")

async def close_mongo_connection():
    """Close database connection"""
    if db.client:
        db.client.close()
        logger.info("Disconnected from MongoDB")

async def create_indexes():
    """Create database indexes for better performance"""
    try:
        # UBO Trace indexes
        await db.database.ubo_traces.create_index("trace_id", unique=True)
        await db.database.ubo_traces.create_index("entity")
        await db.database.ubo_traces.create_index("ubo_name")
        await db.database.ubo_traces.create_index("created_at")
        await db.database.ubo_traces.create_index("status")
        
        # Trace Results indexes
        await db.database.trace_results.create_index("trace_id")
        await db.database.trace_results.create_index("stage")
        await db.database.trace_results.create_index("created_at")
        
        logger.info("Database indexes created successfully")
        
    except Exception as e:
        logger.error(f"Failed to create indexes: {e}")

def get_database() -> AsyncIOMotorDatabase:
    """Get database instance"""
    if db.database is None:
        raise Exception("Database not initialized. Call connect_to_mongo() first.")
    return db.database
