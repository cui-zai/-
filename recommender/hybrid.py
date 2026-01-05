# recommender/hybrid.py
from database.db_operations import get_top_songs, get_new_songs, get_high_rated_songs, get_similar_songs
from database.models import Rating, Song, PlayHistory
from sqlalchemy import func
import random

class HybridRecommender:
    def __init__(self, top_n=10):
        self.top_n = top_n
        self.user_id = None
        
    def train(self, user_id):
        """训练模型（实际是保存用户ID）"""
        self.user_id = user_id
        print(f"🔧 HybridRecommender.train() - 用户ID: {user_id}")
        return True
    
    def recommend_by_type(self, user_id, rec_type):
        """根据类型生成推荐"""
        try:
            print(f"🔧 HybridRecommender.recommend_by_type() - 用户: {user_id}, 类型: {rec_type}")
            
            recommendations = []
            
            if rec_type == 'popular' or rec_type == 'hybrid':
                # 热门歌曲
                songs = get_top_songs(limit=self.top_n)
                for i, song in enumerate(songs):
                    recommendations.append({
                        'song_id': song.id,
                        'id': song.id,
                        'title': song.title,
                        'artist': song.artist,
                        'type': 'popular',
                        'score': 0.8 * (self.top_n - i) / self.top_n
                    })
            
            if rec_type == 'high_rated' or rec_type == 'hybrid':
                # 高评分歌曲
                songs = get_high_rated_songs(limit=self.top_n)
                for i, song in enumerate(songs):
                    score = 0.9 * (song.avg_rating or 0) / 5.0
                    recommendations.append({
                        'song_id': song.id,
                        'id': song.id,
                        'title': song.title,
                        'artist': song.artist,
                        'type': 'high_rated',
                        'score': score if score > 0 else 0.5
                    })
            
            if rec_type == 'new' or rec_type == 'hybrid':
                # 新歌
                songs = get_new_songs(limit=self.top_n)
                for i, song in enumerate(songs):
                    recommendations.append({
                        'song_id': song.id,
                        'id': song.id,
                        'title': song.title,
                        'artist': song.artist,
                        'type': 'new',
                        'score': 0.7 * (self.top_n - i) / self.top_n
                    })
            
            if rec_type == 'collaborative' or rec_type == 'hybrid':
                # 协同过滤（增强版）
                try:
                    print(f"  🔄 尝试协同过滤推荐...")
                    
                    # 获取用户评分过的歌曲
                    user_ratings = Rating.query.filter_by(user_id=user_id).all()
                    print(f"    用户评分记录: {len(user_ratings)} 条")
                    
                    if user_ratings:
                        # 获取用户喜欢的歌曲（评分>=4）
                        liked_songs = [r.song_id for r in user_ratings if r.rating >= 4]
                        print(f"    用户喜欢(评分>=4)的歌曲: {len(liked_songs)} 首")
                        
                        if liked_songs:
                            for song_id in liked_songs[:3]:  # 取前3首喜欢的
                                similar = get_similar_songs(song_id, limit=3)
                                for song in similar:
                                    recommendations.append({
                                        'song_id': song.id,
                                        'id': song.id,
                                        'title': song.title,
                                        'artist': song.artist,
                                        'type': 'collaborative',
                                        'score': 0.85
                                    })
                            print(f"    生成 {len([r for r in recommendations if r['type'] == 'collaborative'])} 条协同过滤推荐")
                        else:
                            print(f"    ⚠️ 用户没有评分>=4的歌曲，使用高评分歌曲替代")
                            # 如果没有喜欢的歌曲，使用高评分歌曲
                            high_songs = get_high_rated_songs(limit=3)
                            for song in high_songs:
                                recommendations.append({
                                    'song_id': song.id,
                                    'id': song.id,
                                    'title': song.title,
                                    'artist': song.artist,
                                    'type': 'collaborative_fallback',
                                    'score': 0.75
                                })
                    else:
                        print(f"    ⚠️ 用户没有评分记录，使用高评分歌曲替代")
                        # 如果没有评分记录，使用高评分歌曲
                        high_songs = get_high_rated_songs(limit=3)
                        for song in high_songs:
                            recommendations.append({
                                'song_id': song.id,
                                'id': song.id,
                                'title': song.title,
                                'artist': song.artist,
                                'type': 'collaborative_fallback',
                                'score': 0.7
                            })
                except Exception as e:
                    print(f"    ❌ 协同过滤错误: {e}")
            
            if rec_type == 'content' or rec_type == 'hybrid':
                # 基于内容的推荐（增强版）
                try:
                    print(f"  🔄 尝试内容推荐...")
                    
                    # 获取用户播放历史中的歌曲
                    history = PlayHistory.query.filter_by(user_id=user_id).order_by(
                        PlayHistory.last_played.desc()
                    ).limit(3).all()
                    
                    print(f"    用户播放历史: {len(history)} 条")
                    
                    if history:
                        for h in history:
                            similar = get_similar_songs(h.song_id, limit=2)
                            for song in similar:
                                recommendations.append({
                                    'song_id': song.id,
                                    'id': song.id,
                                    'title': song.title,
                                    'artist': song.artist,
                                    'type': 'content',
                                    'score': 0.75
                                })
                        print(f"    生成 {len([r for r in recommendations if r['type'] == 'content'])} 条内容推荐")
                    else:
                        print(f"    ⚠️ 用户没有播放历史，使用热门歌曲替代")
                        # 如果没有播放历史，使用热门歌曲
                        pop_songs = get_top_songs(limit=3)
                        for song in pop_songs:
                            recommendations.append({
                                'song_id': song.id,
                                'id': song.id,
                                'title': song.title,
                                'artist': song.artist,
                                'type': 'content_fallback',
                                'score': 0.65
                            })
                except Exception as e:
                    print(f"    ❌ 内容推荐错误: {e}")
            
            # 去重并排序
            seen = set()
            unique_recs = []
            for rec in recommendations:
                if rec['song_id'] not in seen:
                    seen.add(rec['song_id'])
                    unique_recs.append(rec)
            
            # 按评分排序
            unique_recs.sort(key=lambda x: x['score'], reverse=True)
            
            print(f"🔧 生成 {len(unique_recs)} 条推荐（去重后）")
            
            # 如果推荐太少，补充一些随机歌曲
            if len(unique_recs) < self.top_n:
                print(f"  🔄 推荐不足，补充随机歌曲...")
                all_songs = Song.query.order_by(func.random()).limit(self.top_n * 2).all()
                for song in all_songs:
                    if song.id not in seen and len(unique_recs) < self.top_n:
                        unique_recs.append({
                            'song_id': song.id,
                            'id': song.id,
                            'title': song.title,
                            'artist': song.artist,
                            'type': 'random',
                            'score': 0.5
                        })
                        seen.add(song.id)
            
            print(f"🔧 最终推荐数量: {len(unique_recs[:self.top_n])}")
            return unique_recs[:self.top_n]
            
        except Exception as e:
            print(f"❌ HybridRecommender错误: {e}")
            import traceback
            traceback.print_exc()
            return []
