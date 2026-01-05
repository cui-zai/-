"""
数据库初始化脚本
"""
import os
import sys

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.models import db, User, Song, Rating, PlayHistory, UserPreference
from app import app
import random
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash

def init_database():
    """初始化数据库"""
    with app.app_context():
        try:
            # 删除所有表（如果存在）
            db.drop_all()
            print("✅ 已删除旧表")
            
            # 创建所有表
            db.create_all()
            print("✅ 数据库表已创建")
            
            # 创建测试数据
            create_test_data()
            
            print("✅ 测试数据已生成")
            print("🎉 数据库初始化完成！")
            
            # 显示统计信息
            print("\n" + "=" * 50)
            print("📊 数据库统计信息:")
            print("=" * 50)
            print(f"  用户数: {User.query.count()}")
            print(f"  歌曲数: {Song.query.count()}")
            print(f"  评分记录: {Rating.query.count()}")
            print(f"  播放历史: {PlayHistory.query.count()}")
            print("=" * 50)
            
        except Exception as e:
            print(f"❌ 数据库初始化失败: {str(e)}")
            raise

def create_test_data():
    """创建测试数据"""
    # 1. 创建测试用户 - 确保邮箱不重复
    users = []
    base_emails = ['jay', 'jj', 'gem', 'taylor', 'ed', 'weeknd', 'bts', 'bp', 'jaychou', 'jjlin']
    
    for i in range(1, 11):
        username = f'user{i}'
        # 使用不同的邮箱格式避免重复
        email = f'{base_emails[i-1 if i-1 < len(base_emails) else 0]}{i}@music.com'
        
        user = User(
            username=username,
            email=email,
            age=random.randint(18, 40),
            gender=random.choice(['male', 'female']),
            location=random.choice(['北京', '上海', '广州', '深圳', '杭州', '成都']),
            created_at=datetime.utcnow() - timedelta(days=random.randint(1, 365))
        )
        user.set_password('password123')
        users.append(user)
    
    db.session.add_all(users)
    db.session.commit()
    print(f"✅ 创建了 {len(users)} 个测试用户")
    
    # 2. 创建更真实的歌曲数据
    songs_data = [
        # 流行歌曲
        {"title": "七里香", "artist": "周杰伦", "album": "七里香", "genre": "流行", "duration": 240, "release_year": 2004},
        {"title": "青花瓷", "artist": "周杰伦", "album": "我很忙", "genre": "流行", "duration": 235, "release_year": 2007},
        {"title": "告白气球", "artist": "周杰伦", "album": "周杰伦的床边故事", "genre": "流行", "duration": 210, "release_year": 2016},
        {"title": "江南", "artist": "林俊杰", "album": "第二天堂", "genre": "流行", "duration": 264, "release_year": 2004},
        {"title": "她说", "artist": "林俊杰", "album": "她说", "genre": "流行", "duration": 320, "release_year": 2010},
        {"title": "泡沫", "artist": "邓紫棋", "album": "Xposed", "genre": "流行", "duration": 235, "release_year": 2012},
        {"title": "光年之外", "artist": "邓紫棋", "album": "另一个童话", "genre": "流行", "duration": 236, "release_year": 2018},
        
        # 摇滚歌曲
        {"title": "海阔天空", "artist": "Beyond", "album": "乐与怒", "genre": "摇滚", "duration": 319, "release_year": 1993},
        {"title": "无地自容", "artist": "黑豹乐队", "album": "黑豹", "genre": "摇滚", "duration": 284, "release_year": 1991},
        
        # 电子音乐
        {"title": "Fade", "artist": "Alan Walker", "album": "Faded", "genre": "电子", "duration": 249, "release_year": 2014},
        {"title": "Alone", "artist": "Alan Walker", "album": "Alone", "genre": "电子", "duration": 164, "release_year": 2016},
        
        # 英文歌曲
        {"title": "Shape of You", "artist": "Ed Sheeran", "album": "÷", "genre": "流行", "duration": 234, "release_year": 2017},
        {"title": "Perfect", "artist": "Ed Sheeran", "album": "÷", "genre": "流行", "duration": 263, "release_year": 2017},
        {"title": "Blinding Lights", "artist": "The Weeknd", "album": "After Hours", "genre": "流行", "duration": 201, "release_year": 2020},
        {"title": "Bad Guy", "artist": "Billie Eilish", "album": "When We All Fall Asleep", "genre": "流行", "duration": 194, "release_year": 2019},
    ]
    
    songs = []
    for i, song_info in enumerate(songs_data):
        song = Song(
            title=song_info["title"],
            artist=song_info["artist"],
            album=song_info["album"],
            genre=song_info["genre"],
            duration=song_info["duration"],
            release_year=song_info["release_year"],
            play_count=random.randint(100, 10000),
            avg_rating=round(random.uniform(3.5, 5.0), 1),
            created_at=datetime.utcnow() - timedelta(days=random.randint(1, 365))
        )
        songs.append(song)
    
    # 添加一些额外的随机歌曲
    genres = ['流行', '摇滚', '嘻哈', '爵士', '古典', '电子', 'R&B', '民谣', '乡村', '蓝调']
    artists = ['周杰伦', '林俊杰', '邓紫棋', '王力宏', '孙燕姿', '五月天', 'Taylor Swift', 
               'Billie Eilish', 'Ed Sheeran', 'The Weeknd', 'BTS', 'BLACKPINK']
    
    for i in range(len(songs_data) + 1, 101):
        artist = random.choice(artists)
        genre = random.choice(genres)
        
        song = Song(
            title=f'歌曲{i}',
            artist=artist,
            album=f'{artist}的专辑{random.randint(1, 5)}',
            genre=genre,
            duration=random.randint(180, 300),
            release_year=random.randint(2000, 2024),
            play_count=random.randint(100, 5000),
            avg_rating=round(random.uniform(3.0, 5.0), 1),
            created_at=datetime.utcnow() - timedelta(days=random.randint(1, 365))
        )
        songs.append(song)
    
    db.session.add_all(songs)
    db.session.commit()
    print(f"✅ 创建了 {len(songs)} 首歌曲")
    
    # 3. 创建更合理的评分数据
    ratings = []
    for user in users:
        # 根据用户偏好选择歌曲
        liked_genres = random.sample(genres, random.randint(2, 4))
        # 选择相同流派的歌曲
        genre_songs = [song for song in songs if song.genre in liked_genres]
        
        if not genre_songs:
            genre_songs = songs
        
        # 每个用户为15-25首歌评分
        rated_songs = random.sample(genre_songs, min(random.randint(15, 25), len(genre_songs)))
        for song in rated_songs:
            # 用户更可能给喜欢的流派高分
            base_rating = 4.0 if song.genre in liked_genres else 3.0
            rating_value = round(random.uniform(base_rating - 0.5, base_rating + 0.5), 1)
            rating_value = min(5.0, max(1.0, rating_value))
            
            rating = Rating(
                user_id=user.id,
                song_id=song.id,
                rating=rating_value,
                created_at=datetime.utcnow() - timedelta(days=random.randint(1, 100))
            )
            ratings.append(rating)
    
    db.session.add_all(ratings)
    db.session.commit()
    print(f"✅ 创建了 {len(ratings)} 个评分记录")
    
    # 4. 重新计算并更新歌曲平均评分
    update_song_ratings()
    
    # 5. 创建播放历史
    play_histories = []
    for user in users:
        # 获取用户评分较高的歌曲（更可能播放）
        user_ratings = Rating.query.filter_by(user_id=user.id).all()
        high_rated_songs = [r.song_id for r in user_ratings if r.rating >= 4.0]
        
        # 选择播放的歌曲
        if high_rated_songs:
            played_songs = random.sample(
                [song for song in songs if song.id in high_rated_songs], 
                min(random.randint(15, 30), len(high_rated_songs))
            )
        else:
            played_songs = random.sample(songs, min(random.randint(15, 30), len(songs)))
        
        for song in played_songs:
            play_count = random.randint(1, 20)
            history = PlayHistory(
                user_id=user.id,
                song_id=song.id,
                play_count=play_count,
                last_played=datetime.utcnow() - timedelta(days=random.randint(1, 30)),
                total_duration=song.duration * play_count
            )
            play_histories.append(history)
    
    db.session.add_all(play_histories)
    db.session.commit()
    print(f"✅ 创建了 {len(play_histories)} 个播放历史记录")
    
    # 6. 更新歌曲播放次数
    update_song_play_counts()
    
    # 7. 创建用户偏好
    preferences = []
    for user in users:
        # 获取用户播放的歌曲
        user_histories = PlayHistory.query.filter_by(user_id=user.id).all()
        user_song_ids = [h.song_id for h in user_histories]
        user_songs = Song.query.filter(Song.id.in_(user_song_ids)).all()
        
        # 统计流派偏好
        genre_counts = {}
        for song in user_songs:
            if song.genre:
                genre_counts[song.genre] = genre_counts.get(song.genre, 0) + 1
        
        # 计算归一化的偏好分数
        total = sum(genre_counts.values())
        if total > 0:
            genre_preference = {genre: count/total for genre, count in genre_counts.items()}
        else:
            genre_preference = {}
        
        # 创建偏好记录
        import json
        preference = UserPreference(
            user_id=user.id,
            genre_preference=json.dumps(genre_preference),
            updated_at=datetime.utcnow()
        )
        preferences.append(preference)
    
    db.session.add_all(preferences)
    db.session.commit()
    print(f"✅ 创建了 {len(preferences)} 个用户偏好记录")

def update_song_ratings():
    """更新歌曲平均评分"""
    from sqlalchemy import func
    
    songs = Song.query.all()
    updated_count = 0
    
    for song in songs:
        avg_result = db.session.query(func.avg(Rating.rating)).filter(
            Rating.song_id == song.id
        ).first()
        
        avg_rating = avg_result[0] if avg_result[0] is not None else 0.0
        
        if song.avg_rating != avg_rating:
            song.avg_rating = round(avg_rating, 1) if avg_rating else 0.0
            updated_count += 1
    
    db.session.commit()
    print(f"✅ 更新了 {updated_count} 首歌曲的平均评分")

def update_song_play_counts():
    """更新歌曲播放次数"""
    from sqlalchemy import func
    
    songs = Song.query.all()
    updated_count = 0
    
    for song in songs:
        sum_result = db.session.query(func.sum(PlayHistory.play_count)).filter(
            PlayHistory.song_id == song.id
        ).first()
        
        total_plays = sum_result[0] if sum_result[0] is not None else 0
        
        if song.play_count != total_plays:
            song.play_count = total_plays
            updated_count += 1
    
    db.session.commit()
    print(f"✅ 更新了 {updated_count} 首歌曲的播放次数")

if __name__ == '__main__':
    print("=" * 50)
    print("🎵 音乐推荐系统 - 数据库初始化")
    print("=" * 50)
    
    try:
        init_database()
        print("\n🚀 数据库初始化成功完成！")
        print("   现在可以运行 'python app.py' 启动应用了")
    except Exception as e:
        print(f"\n❌ 初始化过程中出现错误: {str(e)}")
        print("   请检查错误信息并重试")
    
    print("=" * 50)