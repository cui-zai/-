"""
API路由
"""
from sqlalchemy import text
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from database.models import db, Song, Rating, PlayHistory, User
from database.db_operations import (
    get_song_by_id, search_songs, add_rating, record_play,
    get_user_play_history, get_system_stats
)
from recommender.hybrid import HybridRecommender
from recommender.popularity import PopularityRecommender
from utils.validators import Validators
import json

api_bp = Blueprint('api', __name__, url_prefix='/api')

# 初始化推荐器
hybrid_recommender = HybridRecommender(top_n=10)
popularity_recommender = PopularityRecommender(top_n=10)

@api_bp.route('/health')
def health_check():
    """健康检查接口"""
    return jsonify({
        'status': 'healthy',
        'message': '音乐推荐系统API运行正常',
        'version': '1.0.0'
    })

@api_bp.route('/test_db')
def test_db():
    """测试数据库连接"""
    try:
        result = db.session.execute(text('SELECT 1')).fetchone()  # 用text()包裹SQL
        return jsonify({
            'status': 'success',
            'message': '数据库连接正常',
            'data': {'test_query': result[0] if result else None}
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'数据库连接失败: {str(e)}'
        }), 500

@api_bp.route('/songs')
def get_songs():
    """获取歌曲列表"""
    try:
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        genre = request.args.get('genre', '')
        artist = request.args.get('artist', '')
        sort_by = request.args.get('sort_by', 'play_count')  # play_count, rating, new
        
        # 构建查询
        query = Song.query
        
        if genre:
            query = query.filter(Song.genre == genre)
        
        if artist:
            query = query.filter(Song.artist == artist)
        
        # 排序
        if sort_by == 'rating':
            query = query.order_by(Song.avg_rating.desc())
        elif sort_by == 'new':
            query = query.order_by(Song.created_at.desc())
        else:  # play_count
            query = query.order_by(Song.play_count.desc())
        
        # 分页
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        songs = pagination.items
        
        # 准备响应数据
        songs_data = []
        for song in songs:
            songs_data.append({
                'id': song.id,
                'title': song.title,
                'artist': song.artist,
                'album': song.album,
                'genre': song.genre,
                'duration': song.duration,
                'release_year': song.release_year,
                'play_count': song.play_count,
                'avg_rating': float(song.avg_rating) if song.avg_rating else 0.0
            })
        
        return jsonify({
            'status': 'success',
            'data': songs_data,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages
            }
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'获取歌曲列表失败: {str(e)}'
        }), 500

@api_bp.route('/songs/<int:song_id>')
def get_song(song_id):
    """获取单个歌曲详情"""
    try:
        song = get_song_by_id(song_id)
        
        if not song:
            return jsonify({
                'status': 'error',
                'message': '歌曲不存在'
            }), 404
        
        # 准备响应数据
        song_data = {
            'id': song.id,
            'title': song.title,
            'artist': song.artist,
            'album': song.album,
            'genre': song.genre,
            'duration': song.duration,
            'release_year': song.release_year,
            'play_count': song.play_count,
            'avg_rating': float(song.avg_rating) if song.avg_rating else 0.0,
            'created_at': song.created_at.isoformat() if song.created_at else None
        }
        
        # 如果有音频特征，也包含
        if song.audio_features:
            try:
                song_data['audio_features'] = json.loads(song.audio_features)
            except:
                pass
        
        return jsonify({
            'status': 'success',
            'data': song_data
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'获取歌曲详情失败: {str(e)}'
        }), 500

@api_bp.route('/songs/search')
def search_songs_api():
    """搜索歌曲"""
    try:
        query = request.args.get('q', '')
        
        if not query:
            return jsonify({
                'status': 'error',
                'message': '搜索关键词不能为空'
            }), 400
        
        # 验证搜索查询
        is_valid, msg = Validators.validate_search_query(query)
        if not is_valid:
            return jsonify({
                'status': 'error',
                'message': msg
            }), 400
        
        # 执行搜索
        songs = search_songs(query, limit=50)
        
        # 准备响应数据
        songs_data = []
        for song in songs:
            songs_data.append({
                'id': song.id,
                'title': song.title,
                'artist': song.artist,
                'album': song.album,
                'genre': song.genre,
                'duration': song.duration,
                'release_year': song.release_year,
                'play_count': song.play_count,
                'avg_rating': float(song.avg_rating) if song.avg_rating else 0.0
            })
        
        return jsonify({
            'status': 'success',
            'data': songs_data,
            'query': query,
            'count': len(songs_data)
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'搜索失败: {str(e)}'
        }), 500

@api_bp.route('/songs/<int:song_id>/rate', methods=['POST'])
@login_required
def rate_song(song_id):
    """为歌曲评分"""
    try:
        data = request.get_json()
        
        if not data or 'rating' not in data:
            return jsonify({
                'status': 'error',
                'message': '缺少评分数据'
            }), 400
        
        # 验证评分
        rating = data['rating']
        is_valid, msg, validated_rating = Validators.validate_rating(rating)
        
        if not is_valid:
            return jsonify({
                'status': 'error',
                'message': msg
            }), 400
        
        # 检查歌曲是否存在
        song = get_song_by_id(song_id)
        if not song:
            return jsonify({
                'status': 'error',
                'message': '歌曲不存在'
            }), 404
        
        # 添加评分
        add_rating(current_user.id, song_id, validated_rating)
        
        return jsonify({
            'status': 'success',
            'message': '评分成功',
            'data': {
                'song_id': song_id,
                'rating': validated_rating,
                'new_avg_rating': float(song.avg_rating) if song.avg_rating else 0.0
            }
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'评分失败: {str(e)}'
        }), 500

@api_bp.route('/songs/<int:song_id>/play', methods=['POST'])
@login_required
def play_song(song_id):
    """记录播放"""
    try:
        data = request.get_json() or {}
        duration = data.get('duration')
        
        # 检查歌曲是否存在
        song = get_song_by_id(song_id)
        if not song:
            return jsonify({
                'status': 'error',
                'message': '歌曲不存在'
            }), 404
        
        # 记录播放历史
        record_play(current_user.id, song_id, duration)
        
        return jsonify({
            'status': 'success',
            'message': '播放记录已保存',
            'data': {
                'song_id': song_id,
                'play_count': song.play_count
            }
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'记录播放失败: {str(e)}'
        }), 500

@api_bp.route('/recommendations')
@login_required
def get_recommendations():
    """获取个性化推荐"""
    try:
        # 获取推荐类型
        rec_type = request.args.get('type', 'hybrid')  # hybrid, collaborative, content, popular, new, high_rated
        
        if rec_type in ['collaborative', 'content', 'hybrid']:
            # 使用混合推荐器
            hybrid_recommender.train(current_user.id)
            recommendations = hybrid_recommender.recommend_by_type(current_user.id, rec_type)
        else:
            # 使用热度推荐器
            popularity_recommender.fit(current_user.id, type=rec_type)
            recommendations = popularity_recommender.recommend(current_user.id)
        
        return jsonify({
            'status': 'success',
            'type': rec_type,
            'data': recommendations,
            'count': len(recommendations)
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'获取推荐失败: {str(e)}'
        }), 500

@api_bp.route('/recommendations/non_personalized')
def get_non_personalized_recommendations():
    """获取非个性化推荐"""
    try:
        rec_type = request.args.get('type', 'popular')  # popular, new, high_rated
        
        popularity_recommender.fit(type=rec_type)
        recommendations = popularity_recommender.recommend()
        
        return jsonify({
            'status': 'success',
            'type': rec_type,
            'data': recommendations,
            'count': len(recommendations)
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'获取推荐失败: {str(e)}'
        }), 500

@api_bp.route('/user/history')
@login_required
def get_user_history():
    """获取用户播放历史"""
    try:
        limit = request.args.get('limit', 50, type=int)
        
        history = get_user_play_history(current_user.id, limit=limit)
        
        # 准备响应数据
        history_data = []
        for record in history:
            song = record.song
            if song:
                history_data.append({
                    'id': record.id,
                    'song_id': song.id,
                    'song_title': song.title,
                    'song_artist': song.artist,
                    'play_count': record.play_count,
                    'last_played': record.last_played.isoformat() if record.last_played else None,
                    'total_duration': record.total_duration
                })
        
        return jsonify({
            'status': 'success',
            'data': history_data,
            'count': len(history_data)
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'获取播放历史失败: {str(e)}'
        }), 500

@api_bp.route('/user/ratings')
@login_required
def get_user_ratings():
    """获取用户评分记录"""
    try:
        ratings = Rating.query.filter_by(user_id=current_user.id).all()
        
        # 准备响应数据
        ratings_data = []
        for rating in ratings:
            song = rating.song
            if song:
                ratings_data.append({
                    'id': rating.id,
                    'song_id': song.id,
                    'song_title': song.title,
                    'song_artist': song.artist,
                    'rating': rating.rating,
                    'rated_at': rating.created_at.isoformat() if rating.created_at else None
                })
        
        return jsonify({
            'status': 'success',
            'data': ratings_data,
            'count': len(ratings_data)
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'获取评分记录失败: {str(e)}'
        }), 500

@api_bp.route('/stats')
def get_stats():
    """获取系统统计信息"""
    try:
        stats = get_system_stats()
        
        return jsonify({
            'status': 'success',
            'data': stats
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'获取统计信息失败: {str(e)}'
        }), 500

@api_bp.route('/genres')
def get_genres():
    """获取所有流派"""
    try:
        # 获取所有非空流派
        genres = db.session.query(Song.genre).filter(
            Song.genre.isnot(None)
        ).distinct().all()
        
        genre_list = [genre[0] for genre in genres if genre[0]]
        
        return jsonify({
            'status': 'success',
            'data': sorted(genre_list),
            'count': len(genre_list)
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'获取流派列表失败: {str(e)}'
        }), 500

@api_bp.route('/artists')
def get_artists():
    """获取所有艺术家"""
    try:
        # 获取查询参数
        limit = request.args.get('limit', 50, type=int)
        
        # 获取热门艺术家（按歌曲数量）
        artists = db.session.query(
            Song.artist,
            db.func.count(Song.id).label('song_count'),
            db.func.sum(Song.play_count).label('total_plays')
        ).group_by(Song.artist
        ).order_by(db.desc('total_plays')
        ).limit(limit).all()
        
        artists_data = []
        for artist, song_count, total_plays in artists:
            artists_data.append({
                'name': artist,
                'song_count': song_count,
                'total_plays': total_plays or 0
            })
        
        return jsonify({
            'status': 'success',
            'data': artists_data,
            'count': len(artists_data)
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'获取艺术家列表失败: {str(e)}'
        }), 500

@api_bp.route('/charts')
def get_charts():
    """获取排行榜"""
    try:
        chart_type = request.args.get('type', 'popular')  # popular, new, high_rated
        limit = request.args.get('limit', 20, type=int)
        
        if chart_type == 'new':
            songs = Song.query.order_by(Song.created_at.desc()).limit(limit).all()
        elif chart_type == 'high_rated':
            # 获取高评分歌曲
            songs = Song.query.filter(
                Song.avg_rating >= 4.0
            ).order_by(Song.avg_rating.desc()).limit(limit).all()
        else:  # popular
            songs = Song.query.order_by(Song.play_count.desc()).limit(limit).all()
        
        # 准备响应数据
        songs_data = []
        for i, song in enumerate(songs):
            songs_data.append({
                'rank': i + 1,
                'id': song.id,
                'title': song.title,
                'artist': song.artist,
                'album': song.album,
                'genre': song.genre,
                'duration': song.duration,
                'play_count': song.play_count,
                'avg_rating': float(song.avg_rating) if song.avg_rating else 0.0
            })
        
        return jsonify({
            'status': 'success',
            'type': chart_type,
            'data': songs_data,
            'count': len(songs_data)
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'获取排行榜失败: {str(e)}'
        }), 500

@api_bp.route('/test_recommendation')
def test_recommendation():
    """测试推荐算法"""
    try:
        # 获取第一个用户（用于测试）
        user = User.query.first()
        
        if not user:
            return jsonify({
                'status': 'error',
                'message': '没有找到用户'
            }), 404
        
        # 测试各种推荐算法
        results = {}
        
        # 热度推荐
        popularity_recommender.fit(type='popular')
        results['popular'] = popularity_recommender.recommend(user.id)
        
        # 新歌推荐
        popularity_recommender.fit(type='new')
        results['new'] = popularity_recommender.recommend(user.id)
        
        # 高评分推荐
        popularity_recommender.fit(type='high_rated')
        results['high_rated'] = popularity_recommender.recommend(user.id)
        
        # 协同过滤推荐
        hybrid_recommender.train(user.id)
        results['collaborative'] = hybrid_recommender.recommend_by_type(user.id, 'collaborative')
        
        # 基于内容的推荐
        results['content'] = hybrid_recommender.recommend_by_type(user.id, 'content')
        
        # 混合推荐
        results['hybrid'] = hybrid_recommender.recommend_by_type(user.id, 'hybrid')
        
        # 统计每种推荐的数量
        stats = {}
        for key, recs in results.items():
            stats[key] = len(recs)
        
        return jsonify({
            'status': 'success',
            'user_id': user.id,
            'username': user.username,
            'stats': stats,
            'data': results
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'测试推荐算法失败: {str(e)}'
        }), 500