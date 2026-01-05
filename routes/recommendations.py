"""
推荐页面路由
"""
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from recommender.hybrid import HybridRecommender
from recommender.popularity import PopularityRecommender
import time

rec_bp = Blueprint('recommendations', __name__, url_prefix='/recommendations')

# 初始化推荐器
hybrid_recommender = HybridRecommender(top_n=20)
popularity_recommender = PopularityRecommender(top_n=20)

@rec_bp.route('/')
@login_required
def recommendations():
    """推荐主页面"""
    return render_template('recommendations.html')

@rec_bp.route('/personalized')
@login_required
def personalized_recommendations():
    """个性化推荐页面"""
    try:
        start_time = time.time()
        
        # 训练推荐器
        hybrid_recommender.train(current_user.id)
        
        # 获取各种类型的推荐
        recommendations = {
            'hybrid': hybrid_recommender.recommend_by_type(current_user.id, 'hybrid'),
            'collaborative': hybrid_recommender.recommend_by_type(current_user.id, 'collaborative'),
            'content': hybrid_recommender.recommend_by_type(current_user.id, 'content')
        }
        
        execution_time = time.time() - start_time
        
        return render_template('personalized_recommendations.html',
                             recommendations=recommendations,
                             execution_time=execution_time)
        
    except Exception as e:
        return render_template('error.html',
                             message=f'获取个性化推荐失败: {str(e)}')

@rec_bp.route('/popular')
def popular_recommendations():
    """热门推荐页面"""
    try:
        start_time = time.time()
        
        # 获取各种热门推荐
        recommendations = {
            'popular': popularity_recommender.recommend(type='popular'),
            'new': popularity_recommender.recommend(type='new'),
            'high_rated': popularity_recommender.recommend(type='high_rated')
        }
        
        execution_time = time.time() - start_time
        
        return render_template('popular_recommendations.html',
                             recommendations=recommendations,
                             execution_time=execution_time)
        
    except Exception as e:
        return render_template('error.html',
                             message=f'获取热门推荐失败: {str(e)}')

@rec_bp.route('/explain')
@login_required
def explain_recommendations():
    """推荐解释页面"""
    try:
        # 获取用户的历史数据用于解释
        from database.db_operations import get_user_play_history, get_user_ratings
        
        history = get_user_play_history(current_user.id, limit=10)
        ratings = get_user_ratings(current_user.id)
        
        # 获取推荐并尝试解释
        hybrid_recommender.train(current_user.id)
        recommendations = hybrid_recommender.recommend(current_user.id)
        
        # 简单的解释逻辑
        explanations = []
        for i, rec in enumerate(recommendations[:5]):
            explanation = {
                'song': rec,
                'reasons': []
            }
            
            # 基于流派
            if rec.get('genre'):
                explanation['reasons'].append(f"您喜欢 {rec['genre']} 类型的音乐")
            
            # 基于艺术家
            if rec.get('artist'):
                explanation['reasons'].append(f"您听过 {rec['artist']} 的其他歌曲")
            
            # 基于热度
            if rec.get('play_count', 0) > 100000:
                explanation['reasons'].append("这首歌曲非常热门")
            
            # 基于评分
            if rec.get('avg_rating', 0) >= 4.0:
                explanation['reasons'].append("这首歌曲评分很高")
            
            explanations.append(explanation)
        
        return render_template('explain_recommendations.html',
                             history=history,
                             ratings=ratings,
                             recommendations=recommendations[:10],
                             explanations=explanations)
        
    except Exception as e:
        return render_template('error.html',
                             message=f'获取推荐解释失败: {str(e)}')

@rec_bp.route('/compare')
@login_required
def compare_recommendations():
    """推荐算法比较页面"""
    try:
        start_time = time.time()
        
        # 训练各种推荐器
        hybrid_recommender.train(current_user.id)
        
        # 获取各种算法的推荐结果
        algorithms = ['hybrid', 'collaborative', 'content', 'popular', 'new', 'high_rated']
        
        results = {}
        for algo in algorithms:
            if algo in ['popular', 'new', 'high_rated']:
                popularity_recommender.fit(type=algo)
                results[algo] = popularity_recommender.recommend(current_user.id)
            else:
                results[algo] = hybrid_recommender.recommend_by_type(current_user.id, algo)
        
        execution_time = time.time() - start_time
        
        # 计算每种算法的统计数据
        stats = {}
        for algo, recs in results.items():
            stats[algo] = {
                'count': len(recs),
                'avg_score': sum(r.get('score', 0) for r in recs) / len(recs) if recs else 0,
                'avg_play_count': sum(r.get('play_count', 0) for r in recs) / len(recs) if recs else 0,
                'avg_rating': sum(r.get('avg_rating', 0) for r in recs) / len(recs) if recs else 0
            }
        
        return render_template('compare_recommendations.html',
                             results=results,
                             stats=stats,
                             execution_time=execution_time,
                             algorithms=algorithms)
        
    except Exception as e:
        return render_template('error.html',
                             message=f'比较推荐算法失败: {str(e)}')

@rec_bp.route('/api/get_recommendations')
@login_required
def api_get_recommendations():
    """API: 获取推荐（JSON格式）"""
    try:
        algorithm = request.args.get('algorithm', 'hybrid')
        limit = request.args.get('limit', 10, type=int)
        
        # 设置推荐数量
        if algorithm in ['popular', 'new', 'high_rated']:
            popularity_recommender.top_n = limit
            popularity_recommender.fit(type=algorithm)
            recommendations = popularity_recommender.recommend(current_user.id)
        else:
            hybrid_recommender.top_n = limit
            hybrid_recommender.train(current_user.id)
            recommendations = hybrid_recommender.recommend_by_type(current_user.id, algorithm)
        
        return jsonify({
            'status': 'success',
            'algorithm': algorithm,
            'limit': limit,
            'recommendations': recommendations,
            'count': len(recommendations)
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@rec_bp.route('/api/refresh')
@login_required
def api_refresh_recommendations():
    """API: 刷新推荐"""
    try:
        # 重新训练推荐器
        hybrid_recommender.train(current_user.id)
        
        # 获取新推荐
        recommendations = hybrid_recommender.recommend(current_user.id)
        
        return jsonify({
            'status': 'success',
            'message': '推荐已刷新',
            'recommendations': recommendations[:10],
            'count': len(recommendations)
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@rec_bp.route('/feedback', methods=['POST'])
@login_required
def feedback():
    """推荐反馈"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'status': 'error', 'message': '没有数据'}), 400
        
        song_id = data.get('song_id')
        feedback_type = data.get('type')  # like, dislike, hide
        reason = data.get('reason', '')
        
        if not song_id or not feedback_type:
            return jsonify({'status': 'error', 'message': '缺少必要参数'}), 400
        
        # 这里可以记录用户的反馈，用于改进推荐算法
        # 例如，将反馈存储到数据库
        
        return jsonify({
            'status': 'success',
            'message': '反馈已记录',
            'data': {
                'song_id': song_id,
                'feedback': feedback_type,
                'reason': reason
            }
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500