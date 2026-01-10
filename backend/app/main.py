import os
from fastapi import FastAPI, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

app = FastAPI()

# Load environment variables
MONGODB_URI = os.getenv("MONGODB_URI", "")
MONGODB_DB = os.getenv("MONGODB_DB", "app")

# MongoDB client (will be initialized on startup)
client = None
db = None


@app.on_event("startup")
async def startup_db_client():
    """Initialize MongoDB connection on startup"""
    global client, db
    if MONGODB_URI:
        try:
            client = AsyncIOMotorClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
            db = client[MONGODB_DB]
            # Test the connection
            await client.admin.command('ping')
            print(f"✓ Connected to MongoDB Atlas (database: {MONGODB_DB})")
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            print(f"✗ MongoDB connection failed: {e}")
            client = None
            db = None
    else:
        print("⚠ MONGODB_URI not set - skipping MongoDB connection")


@app.on_event("shutdown")
async def shutdown_db_client():
    """Close MongoDB connection on shutdown"""
    global client
    if client:
        client.close()
        print("MongoDB connection closed")


@app.get("/health")
async def health():
    """Health check endpoint - returns service and DB status"""
    health_status = {
        "status": "ok",
        "service": "backend",
        "mongodb": {
            "connected": False,
            "database": MONGODB_DB if MONGODB_URI else None
        }
    }
    
    # Test MongoDB connection if client exists
    if client:
        try:
            await client.admin.command('ping')
            health_status["mongodb"]["connected"] = True
        except Exception as e:
            health_status["mongodb"]["error"] = str(e)
    elif not MONGODB_URI:
        health_status["mongodb"]["error"] = "MONGODB_URI not configured"
    else:
        health_status["mongodb"]["error"] = "Connection not initialized"
    
    return health_status


@app.get("/health/db")
async def health_db():
    """Dedicated MongoDB connection test endpoint"""
    if not MONGODB_URI:
        raise HTTPException(status_code=500, detail="MONGODB_URI not configured")
    
    if not client:
        raise HTTPException(status_code=503, detail="MongoDB client not initialized")
    
    try:
        # Ping the database
        result = await client.admin.command('ping')
        # Get database info
        db_info = await db.command('dbStats')
        
        return {
            "status": "connected",
            "mongodb_uri_set": bool(MONGODB_URI),
            "database": MONGODB_DB,
            "ping": result,
            "database_stats": {
                "name": db_info.get("db", MONGODB_DB),
                "collections": db_info.get("collections", 0),
                "data_size": db_info.get("dataSize", 0)
            }
        }
    except ConnectionFailure as e:
        raise HTTPException(status_code=503, detail=f"MongoDB connection failed: {str(e)}")
    except ServerSelectionTimeoutError as e:
        raise HTTPException(status_code=503, detail=f"MongoDB server selection timeout: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"MongoDB error: {str(e)}")
