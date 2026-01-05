# recommender/popularity.py
from database.db_operations import get_top_songs, get_new_songs, get_high_rated_songs

class PopularityRecommender:
    def __init__(self, top_n=10):
        self.top_n = top_n
    
    def fit(self, user_id=None, type='popular'):
        """根据类型准备数据"""
        self.rec_type = type
        print(f"🔧 PopularityRecommender.fit() - 类型: {type}")
        return True
    
    def recommend(self, user_id=None):
        """生成推荐"""
        try:
            print(f"🔧 PopularityRecommender.recommend() - 类型: {self.rec_type}")
            
            if self.rec_type == 'popular':
                # 热门歌曲
                songs = get_top_songs(limit=self.top_n)
                print(f"🔧 获取到 {len(songs)} 首热门歌曲")
                
            elif self.rec_type == 'new':
                # 新歌
                songs = get_new_songs(limit=self.top_n)
                print(f"🔧 获取到 {len(songs)} 首新歌")
                
            elif self.rec_type == 'high_rated':
                # 高评分歌曲
                songs = get_high_rated_songs(limit=self.top_n)
                print(f"🔧 获取到 {len(songs)} 首高评分歌曲")
                
            else:
                songs = []
            
            # 转换为推荐格式
            recommendations = []
            for i, song in enumerate(songs):
                recommendations.append({
                    'song_id': song.id,
                    'id': song.id,
                    'title': song.title,
                    'artist': song.artist,
                    'score': (self.top_n - i) / self.top_n  # 简单评分
                })
            
            print(f"🔧 生成 {len(recommendations)} 条推荐")
            return recommendations
            
        except Exception as e:
            print(f"❌ PopularityRecommender错误: {e}")
            import traceback
            traceback.print_exc()
            return []
