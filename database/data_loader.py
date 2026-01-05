"""
数据加载器 - 用于加载和管理数据集
"""
import csv
import json
import os
from typing import List, Dict, Any
from datetime import datetime

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    print("警告: pandas 未安装，部分功能将不可用")
    
from database.models import db, Song, User, Rating
from database.db_operations import add_song, batch_add_songs
from utils.data_preprocessing import DataPreprocessor
from utils.file_handler import FileHandler

class DataLoader:
    """数据加载器类"""
    
    @staticmethod
    def load_sample_data():
        """加载示例数据到数据库"""
        print("开始加载示例数据...")
        
        # 检查是否已有数据
        if Song.query.count() > 0:
            print("数据库中已有歌曲数据，跳过示例数据加载")
            return
        
        # 示例歌曲数据
        sample_songs = [
            {
                'title': 'Blinding Lights',
                'artist': 'The Weeknd',
                'album': 'After Hours',
                'genre': 'Pop',
                'duration': 200,
                'release_year': 2020,
                'play_count': 1500000
            },
            {
                'title': 'Shape of You',
                'artist': 'Ed Sheeran',
                'album': '÷ (Divide)',
                'genre': 'Pop',
                'duration': 233,
                'release_year': 2017,
                'play_count': 2000000
            },
            {
                'title': 'Bohemian Rhapsody',
                'artist': 'Queen',
                'album': 'A Night at the Opera',
                'genre': 'Rock',
                'duration': 354,
                'release_year': 1975,
                'play_count': 1800000
            },
            {
                'title': 'Billie Jean',
                'artist': 'Michael Jackson',
                'album': 'Thriller',
                'genre': 'Pop',
                'duration': 294,
                'release_year': 1982,
                'play_count': 1600000
            },
            {
                'title': 'Hotel California',
                'artist': 'Eagles',
                'album': 'Hotel California',
                'genre': 'Rock',
                'duration': 391,
                'release_year': 1976,
                'play_count': 1700000
            },
            {
                'title': 'Smells Like Teen Spirit',
                'artist': 'Nirvana',
                'album': 'Nevermind',
                'genre': 'Rock',
                'duration': 301,
                'release_year': 1991,
                'play_count': 1400000
            },
            {
                'title': 'Rolling in the Deep',
                'artist': 'Adele',
                'album': '21',
                'genre': 'Pop',
                'duration': 228,
                'release_year': 2010,
                'play_count': 1900000
            },
            {
                'title': 'Sweet Child O Mine',
                'artist': 'Guns N Roses',
                'album': 'Appetite for Destruction',
                'genre': 'Rock',
                'duration': 356,
                'release_year': 1987,
                'play_count': 1300000
            },
            {
                'title': 'Uptown Funk',
                'artist': 'Mark Ronson ft. Bruno Mars',
                'album': 'Uptown Special',
                'genre': 'Funk',
                'duration': 270,
                'release_year': 2014,
                'play_count': 2100000
            },
            {
                'title': 'Bad Guy',
                'artist': 'Billie Eilish',
                'album': 'When We All Fall Asleep, Where Do We Go?',
                'genre': 'Pop',
                'duration': 194,
                'release_year': 2019,
                'play_count': 2200000
            },
            {
                'title': 'Imagine',
                'artist': 'John Lennon',
                'album': 'Imagine',
                'genre': 'Rock',
                'duration': 183,
                'release_year': 1971,
                'play_count': 1200000
            },
            {
                'title': 'Thriller',
                'artist': 'Michael Jackson',
                'album': 'Thriller',
                'genre': 'Pop',
                'duration': 357,
                'release_year': 1982,
                'play_count': 2300000
            },
            {
                'title': 'Like a Rolling Stone',
                'artist': 'Bob Dylan',
                'album': 'Highway 61 Revisited',
                'genre': 'Folk',
                'duration': 373,
                'release_year': 1965,
                'play_count': 1100000
            },
            {
                'title': 'Hey Jude',
                'artist': 'The Beatles',
                'album': "Hey Jude",
                'genre': 'Rock',
                'duration': 431,
                'release_year': 1968,
                'play_count': 2400000
            },
            {
                'title': 'Purple Rain',
                'artist': 'Prince',
                'album': 'Purple Rain',
                'genre': 'Rock',
                'duration': 512,
                'release_year': 1984,
                'play_count': 1250000
            }
        ]
        
        # 批量添加歌曲
        batch_add_songs(sample_songs)
        print(f"已添加 {len(sample_songs)} 首示例歌曲")
        
        # 添加示例用户（如果不存在）
        if User.query.count() == 0:
            DataLoader.create_sample_users()
        
        # 添加示例评分
        DataLoader.create_sample_ratings()
        
        print("示例数据加载完成！")
    
    @staticmethod
    def create_sample_users():
        """创建示例用户"""
        from werkzeug.security import generate_password_hash
        
        sample_users = [
            {
                'username': 'alice',
                'email': 'alice@example.com',
                'password': 'Alice123!',
                'age': 25,
                'gender': 'female',
                'location': '北京'
            },
            {
                'username': 'bob',
                'email': 'bob@example.com',
                'password': 'Bob123!',
                'age': 30,
                'gender': 'male',
                'location': '上海'
            },
            {
                'username': 'charlie',
                'email': 'charlie@example.com',
                'password': 'Charlie123!',
                'age': 28,
                'gender': 'male',
                'location': '广州'
            },
            {
                'username': 'diana',
                'email': 'diana@example.com',
                'password': 'Diana123!',
                'age': 22,
                'gender': 'female',
                'location': '深圳'
            }
        ]
        
        for user_data in sample_users:
            user = User(
                username=user_data['username'],
                email=user_data['email'],
                password_hash=generate_password_hash(user_data['password']),
                age=user_data['age'],
                gender=user_data['gender'],
                location=user_data['location']
            )
            db.session.add(user)
        
        db.session.commit()
        print(f"已创建 {len(sample_users)} 个示例用户")
    
    @staticmethod
    def create_sample_ratings():
        """创建示例评分"""
        # 获取所有用户和歌曲
        users = User.query.all()
        songs = Song.query.all()
        
        if not users or not songs:
            return
        
        # 为每个用户添加一些评分
        import random
        rating_count = 0
        
        for user in users:
            # 每个用户随机评5-15首歌
            num_ratings = random.randint(5, min(15, len(songs)))
            rated_songs = random.sample(songs, num_ratings)
            
            for song in rated_songs:
                # 随机评分（1-5分，但偏向3-5分）
                rating = random.choices(
                    [1, 2, 3, 4, 5],
                    weights=[0.05, 0.1, 0.2, 0.3, 0.35]
                )[0]
                
                # 检查是否已评分
                existing = Rating.query.filter_by(user_id=user.id, song_id=song.id).first()
                if not existing:
                    rating_record = Rating(
                        user_id=user.id,
                        song_id=song.id,
                        rating=rating
                    )
                    db.session.add(rating_record)
                    rating_count += 1
        
        db.session.commit()
        print(f"已创建 {rating_count} 个示例评分")
    
    @staticmethod
    def load_from_csv(filepath: str):
        """从CSV文件加载数据"""
        if not os.path.exists(filepath):
            print(f"文件不存在: {filepath}")
            return False
        
        try:
            # 使用数据预处理器
            preprocessor = DataPreprocessor()
            df = preprocessor.load_csv(filepath)
            
            if df.empty:
                print("CSV文件为空")
                return False
            
            # 清理数据
            df_clean = preprocessor.clean_music_data(df)
            
            # 转换数据格式
            songs_data = []
            for _, row in df_clean.iterrows():
                song_data = {
                    'title': str(row.get('title', '')),
                    'artist': str(row.get('artist', '')),
                    'album': str(row.get('album', '')) if pd.notna(row.get('album')) else None,
                    'genre': str(row.get('genre', '')) if pd.notna(row.get('genre')) else None,
                    'duration': int(row.get('duration', 180)) if pd.notna(row.get('duration')) else 180,
                    'release_year': int(row.get('release_year')) if pd.notna(row.get('release_year')) else None,
                    'play_count': int(row.get('play_count', 0)) if pd.notna(row.get('play_count')) else 0
                }
                songs_data.append(song_data)
            
            # 批量添加歌曲
            batch_add_songs(songs_data)
            
            print(f"从CSV文件加载了 {len(songs_data)} 首歌曲")
            return True
            
        except Exception as e:
            print(f"加载CSV文件失败: {e}")
            return False
    
    @staticmethod
    def export_to_csv(filepath: str):
        """导出数据到CSV"""
        try:
            # 获取所有歌曲
            songs = Song.query.all()
            
            if not songs:
                print("没有数据可以导出")
                return False
            
            # 准备数据
            data = []
            for song in songs:
                record = {
                    'id': song.id,
                    'title': song.title,
                    'artist': song.artist,
                    'album': song.album or '',
                    'genre': song.genre or '',
                    'duration': song.duration or 0,
                    'release_year': song.release_year or '',
                    'play_count': song.play_count,
                    'avg_rating': float(song.avg_rating) if song.avg_rating else 0.0,
                    'created_at': song.created_at.strftime('%Y-%m-%d %H:%M:%S') if song.created_at else ''
                }
                data.append(record)
            
            # 写入CSV
            FileHandler.write_csv(data, filepath)
            
            print(f"已导出 {len(data)} 条记录到 {filepath}")
            return True
            
        except Exception as e:
            print(f"导出数据失败: {e}")
            return False
    
    @staticmethod
    def generate_test_data(num_users: int = 100, num_songs: int = 1000, 
                          num_ratings: int = 10000):
        """生成测试数据"""
        print(f"开始生成测试数据: {num_users}用户, {num_songs}歌曲, {num_ratings}评分")
        
        import random
        from faker import Faker
        
        fake = Faker()
        
        # 生成歌曲
        if Song.query.count() < num_songs:
            print("生成歌曲数据...")
            songs_data = []
            for i in range(num_songs):
                song_data = {
                    'title': fake.catch_phrase(),
                    'artist': fake.name(),
                    'album': fake.bs() if random.random() > 0.3 else None,
                    'genre': random.choice(['Pop', 'Rock', 'Hip-Hop', 'Jazz', 'Classical', 
                                           'Electronic', 'R&B', 'Country']),
                    'duration': random.randint(120, 480),
                    'release_year': random.randint(1960, 2024),
                    'play_count': random.randint(0, 1000000)
                }
                songs_data.append(song_data)
            
            batch_add_songs(songs_data)
            print(f"已生成 {len(songs_data)} 首歌曲")
        
        # 生成用户
        if User.query.count() < num_users:
            print("生成用户数据...")
            from werkzeug.security import generate_password_hash
            
            for i in range(num_users):
                username = f"user_{i+1:03d}"
                email = f"{username}@test.com"
                
                user = User(
                    username=username,
                    email=email,
                    password_hash=generate_password_hash('Test123!'),
                    age=random.randint(18, 60),
                    gender=random.choice(['male', 'female', 'other']),
                    location=fake.city()
                )
                db.session.add(user)
            
            db.session.commit()
            print(f"已生成 {num_users} 个用户")
        
        # 生成评分
        current_ratings = Rating.query.count()
        if current_ratings < num_ratings:
            print("生成评分数据...")
            
            users = User.query.all()
            songs = Song.query.all()
            
            for i in range(num_ratings - current_ratings):
                user = random.choice(users)
                song = random.choice(songs)
                
                # 检查是否已评分
                existing = Rating.query.filter_by(user_id=user.id, song_id=song.id).first()
                if not existing:
                    rating = random.choices(
                        [1, 2, 3, 4, 5],
                        weights=[0.05, 0.1, 0.2, 0.3, 0.35]
                    )[0]
                    
                    rating_record = Rating(
                        user_id=user.id,
                        song_id=song.id,
                        rating=rating
                    )
                    db.session.add(rating_record)
            
            db.session.commit()
            print(f"已生成 {num_ratings} 个评分")
        
        print("测试数据生成完成！")
    
    @staticmethod
    def clear_all_data():
        """清除所有数据（谨慎使用）"""
        confirm = input("确定要清除所有数据吗？此操作不可恢复！(yes/no): ")
        
        if confirm.lower() != 'yes':
            print("操作已取消")
            return
        
        try:
            # 删除所有记录
            Rating.query.delete()
            from database.models import PlayHistory, UserPreference
            PlayHistory.query.delete()
            UserPreference.query.delete()
            Song.query.delete()
            User.query.delete()
            
            db.session.commit()
            print("所有数据已清除")
            
        except Exception as e:
            db.session.rollback()
            print(f"清除数据失败: {e}")
    
    @staticmethod
    def get_data_statistics():
        """获取数据统计信息"""
        stats = {
            'songs': Song.query.count(),
            'users': User.query.count(),
            'ratings': Rating.query.count(),
            'avg_rating': db.session.query(db.func.avg(Rating.rating)).scalar() or 0,
            'unique_artists': db.session.query(Song.artist).distinct().count(),
            'unique_genres': db.session.query(Song.genre).distinct().count()
        }
        
        return stats

# 命令行接口
if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'load_sample':
            DataLoader.load_sample_data()
        elif command == 'export_csv':
            filepath = sys.argv[2] if len(sys.argv) > 2 else 'music_data.csv'
            DataLoader.export_to_csv(filepath)
        elif command == 'generate_test':
            num_users = int(sys.argv[2]) if len(sys.argv) > 2 else 100
            num_songs = int(sys.argv[3]) if len(sys.argv) > 3 else 1000
            num_ratings = int(sys.argv[4]) if len(sys.argv) > 4 else 10000
            DataLoader.generate_test_data(num_users, num_songs, num_ratings)
        elif command == 'stats':
            stats = DataLoader.get_data_statistics()
            for key, value in stats.items():
                print(f"{key}: {value}")
        elif command == 'clear':
            DataLoader.clear_all_data()
        else:
            print("可用命令:")
            print("  load_sample - 加载示例数据")
            print("  export_csv [filepath] - 导出数据到CSV")
            print("  generate_test [users] [songs] [ratings] - 生成测试数据")
            print("  stats - 显示数据统计")
            print("  clear - 清除所有数据（谨慎使用）")
    else:
        print("请指定命令，如: python data_loader.py load_sample")