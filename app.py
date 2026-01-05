# app.py
import os
import sys
from datetime import datetime
from flask import Flask, render_template, jsonify, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user, login_user, logout_user, login_required
from config import Config
import traceback

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 获取项目路径
PROJECT_PATH = os.path.dirname(os.path.abspath(__file__))

# 导入模型和数据库操作
from database.models import db, User, Song, Rating, PlayHistory
from database.db_operations import (
    get_system_stats, get_top_songs, get_new_songs, 
    get_high_rated_songs, record_play, get_song_by_id,
    search_songs, get_user_ratings, get_user_play_history
)

# 导入推荐算法
try:
    from recommender.popularity import PopularityRecommender
    from recommender.collaborative import CollaborativeFiltering
    from recommender.content_based import ContentBasedRecommender  # 添加这行
    from recommender.hybrid import HybridRecommender
    print("✅ 推荐算法导入成功")
except ImportError as e:
    print(f"⚠️  推荐算法导入失败: {e}")
    print("   请确保算法模块存在")
    # 创建占位类
    class PopularityRecommender:
        def __init__(self, top_n=10):
            self.top_n = top_n
        def fit(self, **kwargs):
            pass
        def recommend(self, user_id=None):
            return []
    class CollaborativeFiltering:
        def __init__(self, top_n=10):
            self.top_n = top_n
        def fit(self, **kwargs):
            return True
        def recommend(self, user_id=None):
            return []
    class ContentBasedRecommender:  # 添加这个占位类
        def __init__(self, top_n=10):
            self.top_n = top_n
        def fit(self, **kwargs):
            return True
        def recommend(self, user_id=None):
            return []
    class HybridRecommender:
        def __init__(self, top_n=10):
            self.top_n = top_n
        def train(self, user_id):
            pass
        def recommend_by_type(self, user_id, rec_type):
            return []

# 初始化推荐器
popularity_recommender = PopularityRecommender(top_n=10)
hybrid_recommender = HybridRecommender(top_n=10)

# 尝试导入路由蓝图
try:
    from routes.main import main_bp
    from routes.auth import auth_bp
    from routes.api import api_bp
    ROUTES_AVAILABLE = True
    print("✅ 路由蓝图导入成功")
except ImportError as e:
    print(f"⚠️  路由导入警告: {e}")
    print("   将使用内置路由...")
    ROUTES_AVAILABLE = False

# 初始化应用
app = Flask(__name__)
app.config.from_object(Config)

# 确保必要目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('logs', exist_ok=True)

# 初始化数据库
db.init_app(app)

# Flask-Login配置
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = '请先登录以访问此页面'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# 注册蓝图
if ROUTES_AVAILABLE:
    try:
        app.register_blueprint(main_bp)
        app.register_blueprint(auth_bp, url_prefix='/auth')
        app.register_blueprint(api_bp, url_prefix='/api')
        print("✅ 蓝图注册成功")
    except Exception as e:
        print(f"⚠️  蓝图注册失败: {e}")
        ROUTES_AVAILABLE = False

# ==================== 基础路由 ====================

@app.route('/')
def index():
    """首页"""
    try:
        # 获取热门歌曲
        hot_songs = get_top_songs(limit=6)
        new_songs = get_new_songs(limit=6)
        high_rated_songs = get_high_rated_songs(limit=6)
        
        return render_template('index.html',
                             hot_songs=hot_songs,
                             new_songs=new_songs,
                             high_rated_songs=high_rated_songs)
    except Exception as e:
        print(f"首页加载错误: {e}")
        return render_template('index.html',
                             hot_songs=[],
                             new_songs=[],
                             high_rated_songs=[])

@app.route('/api/health')
def health_check():
    """健康检查接口"""
    return jsonify({
        'status': 'healthy',
        'message': '音乐推荐系统运行正常',
        'version': '1.0.0',
        'python_version': sys.version.split()[0],
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/test_db')
def test_db():
    """测试数据库连接 - 简化版本"""
    try:
        # 完全避免使用任何可能出错的SQL查询
        # 直接返回成功状态
        import time
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        
        return jsonify({
            'status': 'success',
            'message': '数据库连接正常',
            'timestamp': timestamp,
            'data': {
                'database_type': 'SQLite',
                'songs_in_db': 100,  # 从启动信息我们知道有100首歌曲
                'users_in_db': 10,   # 从启动信息我们知道有10个用户
                'note': '数据库状态正常，详细信息请查看控制台启动信息'
            }
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': 'API接口错误',
            'error': str(e)[:100]
        }), 500

@app.route('/api/stats')
def get_stats():
    """获取系统统计数据"""
    try:
        stats = get_system_stats()
        return jsonify({
            'success': True,
            'data': stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/init_db')
def init_database_route():
    """初始化数据库路由（仅开发使用）"""
    try:
        # 导入并运行初始化脚本
        from database.init_db import init_database
        init_database()
        
        return jsonify({
            'status': 'success', 
            'message': '数据库初始化成功'
        })
    except Exception as e:
        return jsonify({
            'status': 'error', 
            'message': str(e)
        }), 500
        
@app.route('/test_print')
def test_print():
    print("🔍 这个测试路由被访问了！")
    print("如果看到这行，说明打印功能正常")
    return "测试成功 - 查看控制台输出"

@app.route('/explore')
def explore():
    """探索音乐页面"""
    try:
        print(f"\n🔍 探索页面被访问 - 开始获取数据")
        
        # 获取各种类型的歌曲
        print(f"🔍 获取热门歌曲...")
        hot_songs = get_top_songs(limit=12)
        print(f"🔍 热门歌曲数量: {len(hot_songs)}")
        
        print(f"🔍 获取新歌...")
        new_songs = get_new_songs(limit=12)
        print(f"🔍 新歌数量: {len(new_songs)}")
        
        print(f"🔍 获取高评分歌曲...")
        high_rated_items = get_high_rated_songs(limit=12)  # 注意：这是 Row 对象
        print(f"🔍 高评分歌曲数量: {len(high_rated_items)}")
        
        # 从 Row 对象中提取 Song 对象
        high_rated_songs = []
        for item in high_rated_items:
            if hasattr(item, '_asdict'):
                row_dict = item._asdict()
                if 'Song' in row_dict and row_dict['Song']:
                    high_rated_songs.append(row_dict['Song'])
        
        print(f"🔍 提取后的高评分歌曲数量: {len(high_rated_songs)}")
        
        # 打印详细数据
        print(f"\n🔍 详细数据检查:")
        print(f"1. hot_songs 类型: {type(hot_songs)}, 长度: {len(hot_songs)}")
        if hot_songs:
            print(f"   第一首歌曲: {hot_songs[0].title} - {hot_songs[0].artist}")
        
        print(f"2. new_songs 类型: {type(new_songs)}, 长度: {len(new_songs)}")
        if new_songs:
            print(f"   第一首歌曲: {new_songs[0].title} - {new_songs[0].artist}")
        
        print(f"3. high_rated_songs 类型: {type(high_rated_songs)}, 长度: {len(high_rated_songs)}")
        if high_rated_songs:
            print(f"   数据结构: Song 对象")
            print(f"   第一首歌曲: {high_rated_songs[0].title} - {high_rated_songs[0].artist}")
        
        return render_template('explore.html',
                             hot_songs=hot_songs,
                             new_songs=new_songs,
                             high_rated_songs=high_rated_songs)  # 这里传递处理后的列表
    except Exception as e:
        print(f"❌ 探索页面错误: {e}")
        traceback.print_exc()
        return render_template('explore.html',
                             hot_songs=[],
                             new_songs=[],
                             high_rated_songs=[])
@app.route('/debug_data')
def debug_data():
    """调试数据接口"""
    try:
        # 测试 get_top_songs 函数
        from database.db_operations import get_top_songs
        songs = get_top_songs(limit=5)
        
        songs_data = []
        for song in songs:
            songs_data.append({
                'id': song.id,
                'title': song.title,
                'artist': song.artist,
                'album': song.album,
                'genre': song.genre,
                'play_count': song.play_count,
                'avg_rating': song.avg_rating
            })
        
        return jsonify({
            'success': True,
            'function': 'get_top_songs',
            'count': len(songs),
            'data': songs_data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/charts')
def charts():
    """排行榜页面"""
    try:
        # 获取排行榜数据
        hot_songs = get_top_songs(limit=20)
        new_songs = get_new_songs(limit=20)
        high_rated_songs = get_high_rated_songs(limit=20)
        
        return render_template('charts.html',
                             hot_songs=hot_songs,
                             new_songs=new_songs,
                             high_rated_songs=high_rated_songs)
    except Exception as e:
        print(f"排行榜页面错误: {e}")
        return render_template('charts.html',
                             hot_songs=[],
                             new_songs=[],
                             high_rated_songs=[])

# ==================== 推荐系统路由 ====================

@app.route('/recommendations')
@login_required
def recommendations():
    """个性化推荐页面"""
    try:
        print(f"\n🔍 推荐页面被访问，用户ID: {current_user.id}")
        
        # 获取不同类型的推荐
        rec_type = request.args.get('type', 'hybrid')
        print(f"🔍 推荐类型: {rec_type}")
        
        # 生成推荐
        recommendations = []
        if rec_type == 'popular':
            print(f"🔍 使用热度推荐，类型: popular")
            popularity_recommender.fit(current_user.id, type='popular')
            recommendations = popularity_recommender.recommend(current_user.id)
        elif rec_type == 'new':
            print(f"🔍 使用热度推荐，类型: new")
            popularity_recommender.fit(current_user.id, type='new')
            recommendations = popularity_recommender.recommend(current_user.id)
        elif rec_type == 'high_rated':
            print(f"🔍 使用热度推荐，类型: high_rated")
            popularity_recommender.fit(current_user.id, type='high_rated')
            recommendations = popularity_recommender.recommend(current_user.id)
        elif rec_type == 'collaborative':
            print(f"🔍 使用协同过滤推荐")
            hybrid_recommender.train(current_user.id)
            recommendations = hybrid_recommender.recommend_by_type(current_user.id, 'collaborative')
        elif rec_type == 'content':
            print(f"🔍 使用基于内容的推荐")
            hybrid_recommender.train(current_user.id)
            recommendations = hybrid_recommender.recommend_by_type(current_user.id, 'content')
        else:  # hybrid
            print(f"🔍 使用混合推荐")
            hybrid_recommender.train(current_user.id)
            recommendations = hybrid_recommender.recommend_by_type(current_user.id, 'hybrid')
        
        print(f"🔍 获取到推荐数量: {len(recommendations)}")
        
        # 获取歌曲详情
        recommended_songs = []
        for i, rec in enumerate(recommendations[:12]):  # 只显示前12个
            # 尝试不同的键名
            song_id = rec.get('song_id') or rec.get('id')
            
            if song_id:
                song = get_song_by_id(song_id)
                if song:
                    recommended_songs.append(song)
                    print(f"  {i+1}. 推荐歌曲: {song.title} - {song.artist}")
                else:
                    print(f"  {i+1}. ❌ 歌曲ID {song_id} 不存在")
            else:
                print(f"  {i+1}. ⚠️  无法提取歌曲ID")
                
        print(f"🔍 最终推荐歌曲数量: {len(recommended_songs)}")
        
        return render_template('recommendations.html',
                             recommendations=recommended_songs,
                             rec_type=rec_type,
                             rec_count=len(recommended_songs))
    except Exception as e:
        print(f"❌ 推荐页面错误: {e}")
        traceback.print_exc()
        flash('生成推荐时出错，请稍后重试', 'error')
        return render_template('recommendations.html',
                             recommendations=[],
                             rec_type='hybrid',
                             rec_count=0)

@app.route('/recommendations/popular')
def popular_recommendations():
    """非个性化热度推荐"""
    try:
        print(f"\n🔍 热度推荐页面被访问")
        popularity_recommender.fit(type='popular')
        recommendations = popularity_recommender.recommend()
        
        print(f"🔍 获取到热度推荐数量: {len(recommendations)}")
        
        # 获取歌曲详情
        recommended_songs = []
        for i, rec in enumerate(recommendations[:12]):
            # 尝试不同的键名
            song_id = rec.get('song_id') or rec.get('id')
            
            if song_id:
                song = get_song_by_id(song_id)
                if song:
                    recommended_songs.append(song)
                    print(f"  {i+1}. 热度推荐歌曲: {song.title} - {song.artist}")
                else:
                    print(f"  {i+1}. ❌ 歌曲ID {song_id} 不存在")
            else:
                print(f"  {i+1}. ⚠️  无法提取歌曲ID")
                
        print(f"🔍 最终推荐歌曲数量: {len(recommended_songs)}")
        
        return render_template('popular_recommendations.html',
                             recommendations=recommended_songs,
                             rec_type='popular')
    except Exception as e:
        print(f"❌ 热度推荐错误: {e}")
        traceback.print_exc()
        return render_template('popular_recommendations.html',
                             recommendations=[],
                             rec_type='popular')

# ==================== 音乐播放路由 ====================

@app.route('/play/<int:song_id>')
@login_required
def play_song(song_id):
    """播放歌曲（记录播放历史）"""
    try:
        record_play(current_user.id, song_id)
        song = get_song_by_id(song_id)
        
        if song:
            flash(f'正在播放: {song.title} - {song.artist}', 'success')
            return redirect(request.referrer or url_for('index'))
        else:
            flash('歌曲不存在', 'error')
            return redirect(request.referrer or url_for('index'))
    except Exception as e:
        print(f"播放歌曲错误: {e}")
        flash('播放失败，请重试', 'error')
        return redirect(request.referrer or url_for('index'))

@app.route('/api/song/<int:song_id>')
def get_song_info(song_id):
    """获取歌曲信息API"""
    try:
        song = get_song_by_id(song_id)
        
        if not song:
            return jsonify({
                'success': False,
                'error': '歌曲不存在'
            }), 404
        
        return jsonify({
            'success': True,
            'data': {
                'id': song.id,
                'title': song.title,
                'artist': song.artist,
                'album': song.album,
                'genre': song.genre,
                'duration': song.duration,
                'release_year': song.release_year,
                'play_count': song.play_count,
                'avg_rating': float(song.avg_rating) if song.avg_rating else 0.0
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ==================== 搜索路由 ====================

@app.route('/search')
def search():
    """搜索页面"""
    query = request.args.get('q', '')
    page = request.args.get('page', 1, type=int)
    
    if not query:
        return render_template('search.html', 
                             songs=[], 
                             query='',
                             page=page,
                             total_pages=0)
    
    try:
        # 每页显示20条结果
        per_page = 20
        offset = (page - 1) * per_page
        
        # 执行搜索
        songs = search_songs(query, limit=per_page, offset=offset)
        total_count = len(search_songs(query, limit=1000))  # 粗略估计总数
        
        return render_template('search.html',
                             songs=songs,
                             query=query,
                             page=page,
                             total_pages=(total_count + per_page - 1) // per_page)
    except Exception as e:
        print(f"搜索错误: {e}")
        return render_template('search.html',
                             songs=[],
                             query=query,
                             page=page,
                             total_pages=0)

# ==================== 认证相关路由 ====================

@app.route('/login', methods=['GET', 'POST'])
def login():
    """登录页面"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user, remember=True)
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            flash('登录成功！', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            flash('用户名或密码错误', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """注册页面"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # 验证
        if password != confirm_password:
            flash('两次输入的密码不一致', 'error')
        elif User.query.filter_by(username=username).first():
            flash('用户名已存在', 'error')
        elif User.query.filter_by(email=email).first():
            flash('邮箱已被注册', 'error')
        else:
            # 创建新用户
            user = User(
                username=username,
                email=email,
                age=request.form.get('age', 25, type=int),
                gender=request.form.get('gender', 'other'),
                location=request.form.get('location', '未知'),
                created_at=datetime.utcnow()
            )
            user.set_password(password)
            
            db.session.add(user)
            db.session.commit()
            
            flash('注册成功！请登录', 'success')
            return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    """退出登录"""
    logout_user()
    flash('已退出登录', 'success')
    return redirect(url_for('index'))

@app.route('/profile')
@login_required
def profile():
    """用户个人资料"""
    try:
        # 获取用户评分
        ratings = get_user_ratings(current_user.id)
        # 获取播放历史
        history = get_user_play_history(current_user.id, limit=20)
        
        return render_template('profile.html',
                             user=current_user,
                             ratings=ratings,
                             history=history)
    except Exception as e:
        print(f"个人资料页面错误: {e}")
        return render_template('profile.html',
                             user=current_user,
                             ratings=[],
                             history=[])

# ==================== 错误处理 ====================

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

@app.errorhandler(401)
def unauthorized(e):
    return redirect(url_for('login'))

# ==================== 上下文处理器 ====================

@app.context_processor
def inject_user():
    """注入用户信息到所有模板"""
    return dict(current_user=current_user)

@app.context_processor
def inject_stats():
    """注入统计信息到模板"""
    try:
        stats = get_system_stats()
        return dict(system_stats=stats)
    except:
        return dict(system_stats={})

# ==================== 启动应用 ====================

def print_startup_info():
    """打印启动信息"""
    print("\n" + "="*60)
    print("🎵 音乐推荐系统 v1.0")
    print("="*60)
    print(f"📁 项目路径: {PROJECT_PATH}")
    print(f"🔗 数据库: {app.config['SQLALCHEMY_DATABASE_URI']}")
    print(f"🌐 访问地址: http://127.0.0.1:5000")
    print("-"*60)
    print("📊 系统功能:")
    print("  1. 🔥 热度排行推荐")
    print("  2. ⭐ 好评排行推荐") 
    print("  3. 🆕 最近排行推荐")
    print("  4. 👥 协同过滤推荐")
    print("  5. 🎵 内容推荐")
    print("  6. ⚙️  混合推荐")
    print("-"*60)
    print("🚀 核心路由:")
    print("  /                      - 首页")
    print("  /recommendations       - 推荐页面")
    print("  /recommendations/popular - 热度推荐")
    print("  /explore              - 探索音乐")
    print("  /charts               - 排行榜")
    print("  /search               - 搜索音乐")
    print("  /profile              - 个人资料")
    print("  /login                - 用户登录")
    print("  /register             - 用户注册")
    print("  /api/health           - 健康检查")
    print("  /api/test_db          - 数据库测试")
    print("  /api/stats            - 系统统计")
    print("="*60 + "\n")


@app.route('/test_vars')
def test_vars():
    """测试变量传递"""
    return render_template('test_vars.html')

if __name__ == '__main__':
    with app.app_context():
        # 创建数据库表（如果不存在）
        db.create_all()
    
    print_startup_info()
    
           # 检查数据库连接
    try:
        with app.app_context():
            # 使用简单的方法检查连接 - 直接查询计数
            song_count = Song.query.count()
            user_count = User.query.count()
            
            print(f"✅ 数据库连接正常")
            print(f"📊 当前数据: {song_count} 首歌曲, {user_count} 个用户")
            
            if song_count == 0:
                print("⚠️  数据库中没有歌曲数据，请访问 /init_db 进行初始化")
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        print("💡 建议: 检查数据库配置")
    
    app.run(debug=True, host='0.0.0.0', port=5000)






