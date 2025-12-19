"""
MongoDB connection utility for Activity Logs
"""

from pymongo import MongoClient, DESCENDING
from django.conf import settings
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class MongoDBConnection:
    """Singleton MongoDB connection"""
    _instance = None
    _client = None
    _db = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MongoDBConnection, cls).__new__(cls)
            cls._instance._initialize_connection()
        return cls._instance
    
    def _initialize_connection(self):
        """Initialize MongoDB connection"""
        try:
            settings_dict = settings.MONGODB_AUDIT_SETTINGS
            
            # Build connection string
            if settings_dict.get('username') and settings_dict.get('password'):
                connection_string = f"mongodb://{settings_dict['username']}:{settings_dict['password']}@{settings_dict['host']}:{settings_dict['port']}"
            else:
                connection_string = f"mongodb://{settings_dict['host']}:{settings_dict['port']}"
            
            self._client = MongoClient(connection_string, serverSelectionTimeoutMS=5000)
            self._db = self._client[settings_dict['db_name']]
            
            # Test connection
            self._client.server_info()
            logger.info(f"MongoDB connected successfully to {settings_dict['db_name']}")
            
        except Exception as e:
            logger.error(f"MongoDB connection failed: {str(e)}")
            self._client = None
            self._db = None
    
    @property
    def db(self):
        """Get database instance"""
        if self._db is None:
            self._initialize_connection()
        return self._db
    
    @property
    def client(self):
        """Get client instance"""
        if self._client is None:
            self._initialize_connection()
        return self._client
    
    def is_connected(self):
        """Check if MongoDB is connected"""
        try:
            if self._client:
                self._client.server_info()
                return True
        except:
            pass
        return False


# Global MongoDB instance
mongodb = MongoDBConnection()


class ActivityLogManager:
    """Manager for Activity Logs in MongoDB"""
    
    def __init__(self):
        self.collection_name = settings.MONGODB_AUDIT_SETTINGS.get('collection_name', 'activity_logs')
    
    @property
    def collection(self):
        """Get activity logs collection"""
        if mongodb.db is not None:
            return mongodb.db[self.collection_name]
        return None
    
    def create_log(self, **kwargs):
        """Create a new activity log entry"""
        if self.collection is None:
            logger.warning("MongoDB not connected, skipping log creation")
            return None
        
        log_data = {
            'timestamp': kwargs.get('timestamp', datetime.utcnow()),
            'user_id': kwargs.get('user_id'),
            'user_email': kwargs.get('user_email'),
            'user_name': kwargs.get('user_name'),
            'action': kwargs.get('action'),
            'method': kwargs.get('method'),
            'endpoint': kwargs.get('endpoint'),
            'ip_address': kwargs.get('ip_address'),
            'user_agent': kwargs.get('user_agent'),
            'status_code': kwargs.get('status_code'),
            'response_time': kwargs.get('response_time'),
            'request_data': kwargs.get('request_data'),
            'response_data': kwargs.get('response_data'),
            'error_message': kwargs.get('error_message'),
            'model_name': kwargs.get('model_name'),
            'object_id': kwargs.get('object_id'),
            'changes': kwargs.get('changes'),
            'metadata': kwargs.get('metadata', {}),
        }
        
        try:
            result = self.collection.insert_one(log_data)
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Failed to create activity log: {str(e)}")
            return None
    
    def get_logs(self, filters=None, skip=0, limit=50, sort_by='timestamp', sort_order=-1):
        """Get activity logs with filters"""
        if self.collection is None:
            return []
        
        try:
            query = filters or {}
            cursor = self.collection.find(query).sort(sort_by, sort_order).skip(skip).limit(limit)
            logs = []
            for doc in cursor:
                doc['id'] = str(doc['_id'])
                del doc['_id']
                logs.append(doc)
            return logs
        except Exception as e:
            logger.error(f"Failed to get logs: {str(e)}")
            return []
    
    def count_logs(self, filters=None):
        """Count logs matching filters"""
        if self.collection is None:
            return 0
        
        try:
            query = filters or {}
            return self.collection.count_documents(query)
        except Exception as e:
            logger.error(f"Failed to count logs: {str(e)}")
            return 0
    
    def get_audit_trail(self, model_name=None, object_id=None, user_id=None, skip=0, limit=50):
        """Get audit trail for specific object or user"""
        filters = {}
        
        if model_name:
            filters['model_name'] = model_name
        if object_id:
            filters['object_id'] = str(object_id)
        if user_id:
            filters['user_id'] = int(user_id)
        
        return self.get_logs(filters=filters, skip=skip, limit=limit)
    
    def search_logs(self, query, skip=0, limit=50):
        """Search logs by text"""
        if self.collection is None:
            return []
        
        try:
            # Create text search filter
            filters = {
                '$or': [
                    {'action': {'$regex': query, '$options': 'i'}},
                    {'user_email': {'$regex': query, '$options': 'i'}},
                    {'user_name': {'$regex': query, '$options': 'i'}},
                    {'endpoint': {'$regex': query, '$options': 'i'}},
                    {'model_name': {'$regex': query, '$options': 'i'}},
                ]
            }
            return self.get_logs(filters=filters, skip=skip, limit=limit)
        except Exception as e:
            logger.error(f"Failed to search logs: {str(e)}")
            return []
    
    def create_indexes(self):
        """Create indexes for better query performance"""
        if self.collection is None:
            logger.warning("MongoDB not connected, skipping index creation")
            return
        
        try:
            # Create indexes
            self.collection.create_index([('timestamp', DESCENDING)])
            self.collection.create_index([('user_id', DESCENDING)])
            self.collection.create_index([('action', DESCENDING)])
            self.collection.create_index([('model_name', DESCENDING)])
            self.collection.create_index([('object_id', DESCENDING)])
            self.collection.create_index([
                ('action', 'text'),
                ('user_email', 'text'),
                ('endpoint', 'text'),
                ('model_name', 'text')
            ])
            logger.info("MongoDB indexes created successfully")
        except Exception as e:
            logger.error(f"Failed to create indexes: {str(e)}")


# Global activity log manager
activity_log_manager = ActivityLogManager()
