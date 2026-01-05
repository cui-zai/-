"""
路由模块初始化
"""
from routes.auth import auth_bp
from routes.main import main_bp
from routes.recommendations import rec_bp
from routes.api import api_bp

__all__ = ['auth_bp', 'main_bp', 'rec_bp', 'api_bp']