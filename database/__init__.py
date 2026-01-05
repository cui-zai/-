"""
数据库模块初始化
"""
from database.models import db, User, Song, Rating, PlayHistory, UserPreference

__all__ = ['db', 'User', 'Song', 'Rating', 'PlayHistory', 'UserPreference']