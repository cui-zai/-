"""
基础推荐类
"""
from abc import ABC, abstractmethod
import numpy as np
from typing import List, Dict, Any
from database.models import Song

class BaseRecommender(ABC):
    """推荐算法的基类"""
    
    def __init__(self, top_n: int = 10):
        self.top_n = top_n
        self.songs = None
        self.user_history = None
        
    @abstractmethod
    def fit(self, user_id: int = None, **kwargs):
        """训练模型或准备数据"""
        pass
    
    @abstractmethod
    def recommend(self, user_id: int = None, **kwargs) -> List[Dict[str, Any]]:
        """生成推荐"""
        pass
    
    def filter_played_songs(self, user_id: int, candidate_songs: List[Song]) -> List[Song]:
        """过滤用户已播放的歌曲"""
        from database.db_operations import get_user_play_history, get_user_ratings
        
        # 获取用户历史
        history = get_user_play_history(user_id)
        ratings = get_user_ratings(user_id)
        
        played_song_ids = set()
        played_song_ids.update([h.song_id for h in history])
        played_song_ids.update([r.song_id for r in ratings])
        
        # 过滤歌曲
        filtered = [song for song in candidate_songs if song.id not in played_song_ids]
        return filtered
    
    def format_recommendations(self, songs: List[Song], scores: List[float] = None) -> List[Dict[str, Any]]:
        """格式化推荐结果"""
        recommendations = []
        
        for i, song in enumerate(songs):
            if i >= self.top_n:
                break
                
            rec = {
                'id': song.id,
                'title': song.title,
                'artist': song.artist,
                'album': song.album,
                'genre': song.genre,
                'duration': song.duration,
                'play_count': song.play_count,
                'avg_rating': float(song.avg_rating) if song.avg_rating else 0.0,
                'score': float(scores[i]) if scores else 1.0 - (i * 0.01)
            }
            recommendations.append(rec)
        
        return recommendations
    
    def calculate_similarity(self, vector1, vector2):
        """计算向量相似度（余弦相似度）"""
        if not isinstance(vector1, np.ndarray):
            vector1 = np.array(vector1)
        if not isinstance(vector2, np.ndarray):
            vector2 = np.array(vector2)
        
        dot_product = np.dot(vector1, vector2)
        norm1 = np.linalg.norm(vector1)
        norm2 = np.linalg.norm(vector2)
        
        if norm1 == 0 or norm2 == 0:
            return 0
        
        return dot_product / (norm1 * norm2)
    
    def time_decay_factor(self, days_ago: float, half_life: float = 30.0) -> float:
        """计算时间衰减因子"""
        import math
        return math.exp(-math.log(2) * days_ago / half_life)