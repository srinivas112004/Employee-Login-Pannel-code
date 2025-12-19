"""
MongoDB connection utility for chat system
Provides pymongo client and collections for chat models
"""

from pymongo import MongoClient
from django.conf import settings


class MongoDBConnection:
    """Singleton MongoDB connection"""
    _instance = None
    _client = None
    _db = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._client is None:
            self._connect()
    
    def _connect(self):
        """Establish MongoDB connection"""
        mongo_settings = settings.MONGODB_SETTINGS
        
        # Build connection string
        if mongo_settings.get('username') and mongo_settings.get('password'):
            connection_string = f"mongodb://{mongo_settings['username']}:{mongo_settings['password']}@{mongo_settings['host']}:{mongo_settings['port']}/"
        else:
            connection_string = f"mongodb://{mongo_settings['host']}:{mongo_settings['port']}/"
        
        self._client = MongoClient(connection_string)
        self._db = self._client[mongo_settings['db_name']]
        print(f"✅ MongoDB connected to database: {mongo_settings['db_name']}")
    
    @property
    def client(self):
        """Get MongoDB client"""
        return self._client
    
    @property
    def db(self):
        """Get database instance"""
        return self._db
    
    def get_collection(self, collection_name):
        """Get a specific collection"""
        return self._db[collection_name]
    
    def close(self):
        """Close MongoDB connection"""
        if self._client:
            self._client.close()
            print("✅ MongoDB connection closed")


# Global MongoDB instance
def get_mongo_db():
    """Get MongoDB database instance"""
    return MongoDBConnection().db


def get_mongo_collection(collection_name):
    """Get MongoDB collection"""
    return MongoDBConnection().get_collection(collection_name)


# Collection names
CHAT_ROOMS_COLLECTION = 'chat_rooms'
MESSAGES_COLLECTION = 'messages'
ONLINE_STATUS_COLLECTION = 'online_status'
NOTIFICATIONS_COLLECTION = 'notifications'
CHANNELS_COLLECTION = 'channels'  # Department/project channels
