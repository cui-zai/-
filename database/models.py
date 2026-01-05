from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    """用户表"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    age = db.Column(db.Integer)
    gender = db.Column(db.String(10))  # 'male', 'female', 'other'
    location = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # 关系
    ratings = db.relationship('Rating', backref='user', lazy=True, cascade='all, delete-orphan')
    play_history = db.relationship('PlayHistory', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Song(db.Model):
    """歌曲表"""
    __tablename__ = 'songs'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    artist = db.Column(db.String(100), nullable=False)
    album = db.Column(db.String(200))
    genre = db.Column(db.String(50))
    duration = db.Column(db.Integer)  # 秒
    release_year = db.Column(db.Integer)
    play_count = db.Column(db.Integer, default=0)
    avg_rating = db.Column(db.Float, default=0.0)
    rating_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 音频特征（JSON格式存储）
    audio_features = db.Column(db.JSON)
    
    # 关系
    ratings = db.relationship('Rating', backref='song', lazy=True, cascade='all, delete-orphan')
    play_history = db.relationship('PlayHistory', backref='song', lazy=True)
    
    def __repr__(self):
        return f'<Song {self.title} - {self.artist}>'

class Rating(db.Model):
    """评分表"""
    __tablename__ = 'ratings'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    song_id = db.Column(db.Integer, db.ForeignKey('songs.id'), nullable=False)
    rating = db.Column(db.Float, nullable=False)  # 1-5分
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 唯一约束：一个用户对一首歌只能评分一次
    __table_args__ = (db.UniqueConstraint('user_id', 'song_id', name='unique_user_song_rating'),)
    
    def __repr__(self):
        return f'<Rating user:{self.user_id} song:{self.song_id} rating:{self.rating}>'

class PlayHistory(db.Model):
    """播放历史表"""
    __tablename__ = 'play_history'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    song_id = db.Column(db.Integer, db.ForeignKey('songs.id'), nullable=False)
    play_count = db.Column(db.Integer, default=1)
    last_played = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    total_duration = db.Column(db.Integer, default=0)  # 总播放时长（秒）
    
    def __repr__(self):
        return f'<PlayHistory user:{self.user_id} song:{self.song_id} count:{self.play_count}>'

class UserPreference(db.Model):
    """用户偏好表"""
    __tablename__ = 'user_preferences'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    genre_preference = db.Column(db.JSON)  # 流派偏好
    artist_preference = db.Column(db.JSON)  # 艺术家偏好
    tempo_preference = db.Column(db.String(50))  # 节奏偏好
    mood_preference = db.Column(db.String(50))   # 心情偏好
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = db.relationship('User', backref='preference', uselist=False)
    
    def __repr__(self):
        return f'<UserPreference user:{self.user_id}>'
