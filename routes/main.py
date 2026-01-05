"""
主要路由
"""
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from database.models import Song, Rating, PlayHistory
from database.db_operations import get_system_stats, search_songs, get_top_songs
from utils.validators import Validators

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """首页"""
    # 获取热门歌曲（用于展示）
    hot_songs = get_top_songs(limit=10)
    
    # 获取系统统计
    stats = get_system_stats()
    
    return render_template('index.html', 
                         hot_songs=hot_songs,
                         stats=stats)

@main_bp.route('/dashboard')
@login_required
def dashboard():
    """用户仪表板"""
    # 获取用户最近播放
    from database.db_operations import get_user_play_history
    recent_plays = get_user_play_history(current_user.id, limit=10)
    
    # 获取用户评分
    user_ratings = Rating.query.filter_by(user_id=current_user.id).order_by(
        Rating.created_at.desc()
    ).limit(10).all()
    
    # 获取推荐（这里简单实现，实际应该使用推荐算法）
    recommended_songs = get_top_songs(limit=10)
    
    return render_template('dashboard.html',
                         recent_plays=recent_plays,
                         user_ratings=user_ratings,
                         recommended_songs=recommended_songs)

# @main_bp.route('/explore')
# def explore():
#     """探索页面"""
#     # 获取查询参数
#     page = request.args.get('page', 1, type=int)
#     genre = request.args.get('genre', '')
#     artist = request.args.get('artist', '')
#     sort_by = request.args.get('sort_by', 'popular')
    
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
    else:  # popular
        query = query.order_by(Song.play_count.desc())
    
    # 分页
    per_page = 20
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    songs = pagination.items
    
    # 获取所有流派（用于筛选）
    genres = Song.query.with_entities(Song.genre).filter(
        Song.genre.isnot(None)
    ).distinct().all()
    genre_list = [g[0] for g in genres if g[0]]
    
    # 获取热门艺术家（用于筛选）
    artists = Song.query.with_entities(Song.artist).filter(
        Song.artist.isnot(None)
    ).distinct().limit(50).all()
    artist_list = [a[0] for a in artists if a[0]]
    
    return render_template('explore.html',
                         songs=songs,
                         pagination=pagination,
                         genres=sorted(genre_list),
                         artists=sorted(artist_list),
                         current_genre=genre,
                         current_artist=artist,
                         current_sort=sort_by)

@main_bp.route('/charts')
def charts():
    """排行榜页面"""
    # 获取不同类型的排行榜
    popular_songs = Song.query.order_by(Song.play_count.desc()).limit(20).all()
    
    new_songs = Song.query.order_by(Song.created_at.desc()).limit(20).all()
    
    high_rated_songs = Song.query.filter(
        Song.avg_rating >= 3.5
    ).order_by(Song.avg_rating.desc()).limit(20).all()
    
    return render_template('charts.html',
                         popular_songs=popular_songs,
                         new_songs=new_songs,
                         high_rated_songs=high_rated_songs)

@main_bp.route('/search')
def search():
    """搜索页面"""
    query = request.args.get('q', '')
    
    if not query:
        return render_template('search.html', query='', results=[])
    
    # 验证搜索查询
    is_valid, msg = Validators.validate_search_query(query)
    if not is_valid:
        flash(msg, 'warning')
        return render_template('search.html', query=query, results=[])
    
    # 执行搜索
    results = search_songs(query, limit=100)
    
    return render_template('search.html',
                         query=query,
                         results=results,
                         result_count=len(results))

@main_bp.route('/song/<int:song_id>')
def song_detail(song_id):
    """歌曲详情页"""
    from database.db_operations import get_song_by_id
    
    song = get_song_by_id(song_id)
    
    if not song:
        flash('歌曲不存在', 'danger')
        return redirect(url_for('main.explore'))
    
    # 获取相似歌曲（基于相同流派）
    similar_songs = Song.query.filter(
        Song.genre == song.genre,
        Song.id != song.id
    ).order_by(Song.play_count.desc()).limit(10).all()
    
    # 获取用户评分（如果已登录）
    user_rating = None
    if current_user.is_authenticated:
        rating = Rating.query.filter_by(
            user_id=current_user.id,
            song_id=song_id
        ).first()
        if rating:
            user_rating = rating.rating
    
    return render_template('song_detail.html',
                         song=song,
                         similar_songs=similar_songs,
                         user_rating=user_rating)

@main_bp.route('/artist/<artist_name>')
def artist_detail(artist_name):
    """艺术家详情页"""
    # 获取艺术家的所有歌曲
    songs = Song.query.filter_by(artist=artist_name).order_by(
        Song.play_count.desc()
    ).all()
    
    if not songs:
        flash('未找到该艺术家的歌曲', 'warning')
        return redirect(url_for('main.explore'))
    
    # 计算艺术家统计信息
    total_plays = sum(song.play_count for song in songs)
    avg_rating = sum(song.avg_rating or 0 for song in songs) / len(songs) if songs else 0
    
    return render_template('artist_detail.html',
                         artist_name=artist_name,
                         songs=songs,
                         total_plays=total_plays,
                         avg_rating=avg_rating,
                         song_count=len(songs))

@main_bp.route('/genre/<genre_name>')
def genre_detail(genre_name):
    """流派详情页"""
    # 获取该流派的所有歌曲
    songs = Song.query.filter_by(genre=genre_name).order_by(
        Song.play_count.desc()
    ).all()
    
    if not songs:
        flash('未找到该流派的歌曲', 'warning')
        return redirect(url_for('main.explore'))
    
    # 获取该流派的艺术家
    artists = Song.query.with_entities(Song.artist).filter(
        Song.genre == genre_name
    ).distinct().all()
    artist_list = [a[0] for a in artists if a[0]]
    
    return render_template('genre_detail.html',
                         genre_name=genre_name,
                         songs=songs,
                         artists=artist_list,
                         song_count=len(songs))

@main_bp.route('/play_history')
@login_required
def play_history():
    """播放历史页面"""
    from database.db_operations import get_user_play_history
    
    # 获取播放历史
    history = get_user_play_history(current_user.id, limit=100)
    
    # 统计信息
    total_plays = sum(h.play_count for h in history)
    total_duration = sum(h.total_duration for h in history)
    
    return render_template('play_history.html',
                         history=history,
                         total_plays=total_plays,
                         total_duration=total_duration)

@main_bp.route('/favorites')
@login_required
def favorites():
    """收藏页面"""
    # 获取用户评分较高的歌曲（>=4分）
    favorites = Rating.query.filter_by(
        user_id=current_user.id
    ).filter(Rating.rating >= 4).order_by(
        Rating.rating.desc()
    ).all()
    
    favorite_songs = []
    for fav in favorites:
        if fav.song:
            favorite_songs.append({
                'song': fav.song,
                'rating': fav.rating,
                'rated_at': fav.created_at
            })
    
    return render_template('favorites.html', favorite_songs=favorite_songs)

@main_bp.route('/settings')
@login_required
def settings():
    """设置页面"""
    return render_template('settings.html')

@main_bp.route('/about')
def about():
    """关于页面"""
    return render_template('about.html')

@main_bp.route('/help')
def help_page():
    """帮助页面"""
    return render_template('help.html')

@main_bp.route('/api_test')
def api_test():
    """API测试页面（开发用）"""
    return render_template('api_test.html')

@main_bp.route('/system_status')
def system_status():
    """系统状态页面"""
    stats = get_system_stats()
    
    return render_template('system_status.html', stats=stats)

# 错误处理页面
@main_bp.app_errorhandler(404)
def page_not_found(e):
    return render_template('errors/404.html'), 404

@main_bp.app_errorhandler(500)
def internal_server_error(e):
    return render_template('errors/500.html'), 500

@main_bp.app_errorhandler(403)
def forbidden(e):
    return render_template('errors/403.html'), 403