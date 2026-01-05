# database/db_operations.py
from datetime import datetime, timedelta
from sqlalchemy import desc, func, or_
from .models import db, User, Song, Rating, PlayHistory, UserPreference
import json

def get_system_stats():
    """获取系统统计信息"""
    try:
        # 基本统计
        total_songs = Song.query.count()
        total_users = User.query.count()
        total_ratings = Rating.query.count()
        
        # 总播放量
        plays_sum = db.session.query(func.sum(Song.play_count)).scalar()
        total_plays = int(plays_sum) if plays_sum else 0
        
        # 平均评分
        avg_rating_result = db.session.query(func.avg(Rating.rating)).scalar()
        avg_rating = round(float(avg_rating_result), 2) if avg_rating_result else 0.0
        
        stats = {
            'total_songs': total_songs,
            'total_users': total_users,
            'total_ratings': total_ratings,
            'total_plays': total_plays,
            'avg_rating': avg_rating,
            'system_status': 'running',
            'last_updated': datetime.now().isoformat()
        }
        
        return stats
        
    except Exception as e:
        print(f"获取系统统计错误: {e}")
        return {
            'total_songs': 0,
            'total_users': 0,
            'total_ratings': 0,
            'total_plays': 0,
            'avg_rating': 0.0,
            'system_status': 'error',
            'error': str(e)
        }

def get_top_songs(limit=10):
    """获取热门歌曲（按播放次数排序）"""
    return Song.query.order_by(Song.play_count.desc()).limit(limit).all()

def get_new_songs(limit=10):
    """获取新歌曲（按创建时间排序）"""
    return Song.query.order_by(Song.created_at.desc()).limit(limit).all()

def get_high_rated_songs(limit=10):
    """获取高评分歌曲（按平均评分排序）"""
    return Song.query.order_by(Song.avg_rating.desc()).limit(limit).all()

def get_song_by_id(song_id):
    """根据ID获取歌曲"""
    return Song.query.get(song_id)

def record_play(user_id, song_id):
    """记录播放历史"""
    try:
        # 更新歌曲播放次数
        song = Song.query.get(song_id)
        if song:
            song.play_count = (song.play_count or 0) + 1
            song.last_played = datetime.utcnow()
            db.session.commit()
            return True
        return False
    except Exception as e:
        print(f"记录播放错误: {e}")
        db.session.rollback()
        return False

def search_songs(query, limit=20, offset=0):
    """搜索歌曲"""
    if not query:
        return []
    
    search_pattern = f"%{query}%"
    return Song.query.filter(
        or_(
            Song.title.ilike(search_pattern),
            Song.artist.ilike(search_pattern),
            Song.album.ilike(search_pattern),
            Song.genre.ilike(search_pattern)
        )
    ).limit(limit).offset(offset).all()

def get_user_ratings(user_id, limit=20):
    """获取用户评分"""
    return Rating.query.filter_by(user_id=user_id).order_by(
        Rating.created_at.desc()
    ).limit(limit).all()

def get_user_play_history(user_id, limit=20):
    """获取用户播放历史"""
    return PlayHistory.query.filter_by(user_id=user_id).order_by(
        PlayHistory.last_played.desc()
    ).limit(limit).all()
