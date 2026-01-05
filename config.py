import os
from datetime import timedelta

# 基础路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class Config:
    # 应用配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'music-recommendation-secret-key-2024'
    DEBUG = True
    
    # 数据库配置 - 改为SQLite避免MySQL连接问题
    SQLALCHEMY_DATABASE_URI = 'sqlite:///music_recommendation.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 会话配置
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
    # 文件上传
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static/uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp3'}
    
    # 推荐系统配置
    TOP_N = 10  # 推荐列表长度
    SIMILARITY_THRESHOLD = 0.7
    POPULARITY_DAYS = 30
    
    # 日志配置
    LOG_FILE = os.path.join(BASE_DIR, 'logs/app.log')
    LOG_LEVEL = 'INFO'
    
    # 邮件配置（可选）
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    
    # 分页配置
    ITEMS_PER_PAGE = 20