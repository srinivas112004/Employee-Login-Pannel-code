"""
Database router for MongoDB integration
Routes chat app models to MongoDB, everything else to SQLite/PostgreSQL
"""


class ChatMongoRouter:
    """
    A router to control all database operations on models in the chat application.
    """
    
    route_app_labels = {'chat'}
    
    def db_for_read(self, model, **hints):
        """
        Attempts to read chat models go to MongoDB.
        """
        if model._meta.app_label in self.route_app_labels:
            return 'mongodb'
        return None
    
    def db_for_write(self, model, **hints):
        """
        Attempts to write chat models go to MongoDB.
        """
        if model._meta.app_label in self.route_app_labels:
            return 'mongodb'
        return None
    
    def allow_relation(self, obj1, obj2, **hints):
        """
        Allow relations if a model in the chat app is involved.
        """
        if (
            obj1._meta.app_label in self.route_app_labels or
            obj2._meta.app_label in self.route_app_labels
        ):
            return True
        return None
    
    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Make sure the chat app only appears in the 'mongodb' database.
        """
        if app_label in self.route_app_labels:
            return db == 'mongodb'
        return None
