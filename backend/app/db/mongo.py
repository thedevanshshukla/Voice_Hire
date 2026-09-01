import os
from typing import Optional, List, Dict, Any
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.config import settings
from app.models.interview import InterviewSession
from app.models.user import User
from app.core.logger import get_logger

logger = get_logger("db.mongo")

class MongoDBClientManager:
    """Manages Async Motor MongoDB Client lifecycle with graceful in-memory fallback."""
    def __init__(self):
        self._client: Optional[AsyncIOMotorClient] = None
        self._db: Optional[AsyncIOMotorDatabase] = None
        self._is_connected: bool = False
        self._in_memory_sessions: Dict[str, Dict[str, Any]] = {}
        self._in_memory_users: Dict[str, Dict[str, Any]] = {}

    def get_database(self) -> Optional[AsyncIOMotorDatabase]:
        if not self._client:
            try:
                uri = settings.MONGODB_URI
                if uri and not uri.startswith("your-"):
                    self._client = AsyncIOMotorClient(uri, serverSelectionTimeoutMS=3000)
                    self._db = self._client[settings.MONGODB_DB_NAME]
                    self._is_connected = True
                    logger.info("Connected to MongoDB cluster", extra={"db": settings.MONGODB_DB_NAME})
            except Exception as e:
                logger.warning(f"MongoDB connection failed; falling back to in-memory store: {e}")
                self._is_connected = False
        return self._db

db_manager = MongoDBClientManager()

class UserRepository:
    """Repository for user accounts."""
    
    @staticmethod
    async def create_user(user: User) -> User:
        db = db_manager.get_database()
        doc = user.model_dump()
        
        if db is not None:
            try:
                await db.users.insert_one(doc)
                logger.info(f"User {user.email} saved to MongoDB")
                return user
            except Exception as e:
                logger.warning(f"Failed to persist user to MongoDB: {e}")
                
        db_manager._in_memory_users[user.email] = doc
        return user

    @staticmethod
    async def get_user_by_email(email: str) -> Optional[User]:
        db = db_manager.get_database()
        if db is not None:
            try:
                doc = await db.users.find_one({"email": email.lower().strip()}, {"_id": 0})
                if doc:
                    return User(**doc)
            except Exception as e:
                logger.warning(f"Error querying user by email in MongoDB: {e}")
                
        doc = db_manager._in_memory_users.get(email.lower().strip())
        return User(**doc) if doc else None

    @staticmethod
    async def get_user_by_id(user_id: str) -> Optional[User]:
        db = db_manager.get_database()
        if db is not None:
            try:
                doc = await db.users.find_one({"user_id": user_id}, {"_id": 0})
                if doc:
                    return User(**doc)
            except Exception as e:
                logger.warning(f"Error querying user by id in MongoDB: {e}")
                
        for doc in db_manager._in_memory_users.values():
            if doc.get("user_id") == user_id:
                return User(**doc)
        return None

class InterviewSessionRepository:
    """Repository for persisting and retrieving InterviewSession documents."""
    
    @staticmethod
    async def create_session(session: InterviewSession) -> InterviewSession:
        db = db_manager.get_database()
        doc = session.model_dump()
        
        if db is not None:
            try:
                await db.interview_sessions.insert_one(doc)
                logger.info(f"Session {session.session_id} persisted to MongoDB")
                return session
            except Exception as e:
                logger.warning(f"Failed to persist to MongoDB, storing in memory: {e}")
                
        db_manager._in_memory_sessions[session.session_id] = doc
        return session

    @staticmethod
    async def get_session(session_id: str) -> Optional[InterviewSession]:
        db = db_manager.get_database()
        if db is not None:
            try:
                doc = await db.interview_sessions.find_one({"session_id": session_id}, {"_id": 0})
                if doc:
                    return InterviewSession(**doc)
            except Exception as e:
                logger.warning(f"Error querying MongoDB: {e}")
                
        doc = db_manager._in_memory_sessions.get(session_id)
        return InterviewSession(**doc) if doc else None

    @staticmethod
    async def update_session(session_id: str, updates: Dict[str, Any]) -> Optional[InterviewSession]:
        db = db_manager.get_database()
        if db is not None:
            try:
                await db.interview_sessions.update_one(
                    {"session_id": session_id},
                    {"$set": updates}
                )
                return await InterviewSessionRepository.get_session(session_id)
            except Exception as e:
                logger.warning(f"MongoDB update failed: {e}")

        if session_id in db_manager._in_memory_sessions:
            db_manager._in_memory_sessions[session_id].update(updates)
            return InterviewSession(**db_manager._in_memory_sessions[session_id])
        return None

    @staticmethod
    async def list_sessions(
        candidate_id: Optional[str] = None,
        user_email: Optional[str] = None,
        limit: int = 50
    ) -> List[InterviewSession]:
        db = db_manager.get_database()
        sessions = []
        
        query: Dict[str, Any] = {}
        if candidate_id:
            query["candidate_id"] = candidate_id
        if user_email:
            query["user_email"] = user_email.lower().strip()
            
        if db is not None:
            try:
                cursor = db.interview_sessions.find(query, {"_id": 0}).sort("created_at", -1).limit(limit)
                async for doc in cursor:
                    sessions.append(InterviewSession(**doc))
                return sessions
            except Exception as e:
                logger.warning(f"MongoDB list query failed: {e}")

        # In-memory fallback
        for doc in db_manager._in_memory_sessions.values():
            if candidate_id and doc.get("candidate_id") != candidate_id:
                continue
            if user_email and doc.get("user_email") != user_email.lower().strip():
                continue
            sessions.append(InterviewSession(**doc))
        return sorted(sessions, key=lambda s: s.created_at, reverse=True)[:limit]
