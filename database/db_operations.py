# database/db_operations.py
from .models import db, Song, Rating, PlayHistory, User
from sqlalchemy import func, desc, or_
from werkzeug.security import generate_password_hash, check_password_hash


def get_system_stats():
    """获取系统统计信息"""
    try:
        print("🔍 get_system_stats被调用")
        
        # 1. 获取基本统计
        total_songs = Song.query.count()
        total_users = User.query.count()
        total_ratings = Rating.query.count()
        
        print(f"   歌曲总数查询: {total_songs}")
        print(f"   用户总数查询: {total_users}")
        print(f"   评分总数查询: {total_ratings}")
        
        # 2. 获取总播放量（处理可能为None的情况）
        total_plays_result = db.session.query(func.sum(Song.play_count)).scalar()
        total_plays = int(total_plays_result) if total_plays_result else 0
        
        print(f"   总播放量查询: {total_plays}")
        
        # 3. 获取有评分的歌曲数量
        rated_songs_result = db.session.query(func.count(func.distinct(Rating.song_id))).scalar()
        rated_songs = int(rated_songs_result) if rated_songs_result else 0
        
        print(f"   有评分的歌曲数: {rated_songs}")
        
        # 4. 获取系统平均评分
        avg_rating_result = db.session.query(func.avg(Rating.rating)).scalar()
        avg_system_rating = round(float(avg_rating_result), 1) if avg_rating_result else 0.0
        
        print(f"   系统平均评分: {avg_system_rating}")
        
        # 5. 获取最高评分的歌曲
        top_rated_song = None
        try:
            # 先获取有评分记录的歌曲
            songs_with_ratings = db.session.query(Song).join(Rating).group_by(Song.id)
            top_rated_song = songs_with_ratings.order_by(Song.avg_rating.desc()).first()
            if top_rated_song:
                print(f"   最高评分歌曲: {top_rated_song.title} ({top_rated_song.avg_rating})")
        except Exception as e:
            print(f"   获取最高评分歌曲错误: {e}")
            # 如果上面的方法失败，尝试简单方法
            top_rated_song = Song.query.filter(Song.avg_rating > 0).order_by(Song.avg_rating.desc()).first()
        
        # 6. 获取播放最多的歌曲
        most_played_song = Song.query.order_by(Song.play_count.desc()).first()
        if most_played_song:
            print(f"   播放最多歌曲: {most_played_song.title} ({most_played_song.play_count})")
        
        stats = {
            'total_songs': total_songs,
            'total_users': total_users,
            'total_ratings': total_ratings,
            'total_plays': total_plays,
            'rated_songs': rated_songs,
            'avg_system_rating': avg_system_rating,
            'top_rated_song': top_rated_song,
            'most_played_song': most_played_song
        }
        
        print(f"🔍 返回统计: {stats}")
        return stats
        
    except Exception as e:
        print(f"❌ get_system_stats错误: {e}")
        import traceback
        traceback.print_exc()
        
        # 返回默认值
        return {
            'total_songs': 0,
            'total_users': 0,
            'total_ratings': 0,
            'total_plays': 0,
            'rated_songs': 0,
            'avg_system_rating': 0.0,
            'top_rated_song': None,
            'most_played_song': None
        }


def get_top_songs(limit=10):
    """获取热门歌曲（按播放次数排序）"""
    try:
        return Song.query.order_by(Song.play_count.desc()).limit(limit).all()
    except Exception as e:
        print(f"热门歌曲查询错误: {e}")
        return []


def get_new_songs(limit=10):
    """获取最新歌曲（按创建时间排序）"""
    try:
        return Song.query.order_by(Song.created_at.desc()).limit(limit).all()
    except Exception as e:
        print(f"新歌查询错误: {e}")
        return []


def get_high_rated_songs(limit=10):
    """获取高评分歌曲（按平均评分排序）- 保证返回Song对象"""
    try:
        print(f"🔍 get_high_rated_songs被调用，limit={limit}")
        
        # 方法1：直接查询Song表（最简单，最可靠）
        from sqlalchemy import and_
        
        query = Song.query.filter(
            and_(
                Song.rating_count > 0,
                Song.avg_rating > 0
            )
        ).order_by(Song.avg_rating.desc()).limit(limit)
        
        songs = query.all()
        print(f"  查询到 {len(songs)} 首有评分歌曲")
        
        if songs and len(songs) > 0:
            # 验证返回的是Song对象
            first_item = songs[0]
            if hasattr(first_item, '_asdict'):
                # 如果是Row对象，提取Song对象
                print(f"  ⚠️ 检测到Row对象，进行转换...")
                song_list = []
                for item in songs:
                    if hasattr(item, '_asdict'):
                        row_dict = item._asdict()
                        if 'Song' in row_dict:
                            song_list.append(row_dict['Song'])
                        else:
                            # 尝试其他可能的键
                            for key, value in row_dict.items():
                                if isinstance(value, Song):
                                    song_list.append(value)
                                    break
                if song_list:
                    print(f"  ✅ 成功转换出 {len(song_list)} 首Song对象")
                    return song_list[:limit]
            else:
                # 已经是Song对象
                print(f"  ✅ 返回的是 {len(songs)} 首Song对象")
                return songs
        
        # 方法2：如果上面的查询没结果，放宽条件
        print("  🔄 尝试放宽查询条件...")
        songs = Song.query.filter(Song.avg_rating > 0).order_by(Song.avg_rating.desc()).limit(limit).all()
        
        if songs and len(songs) > 0:
            print(f"  ✅ 找到 {len(songs)} 首平均分>0的歌曲")
            return songs
        
        # 方法3：如果还是没有，返回播放最多的歌曲作为备用
        print("  🔄 使用热门歌曲作为备用...")
        songs = Song.query.order_by(Song.play_count.desc()).limit(limit).all()
        print(f"  ⚠️  使用 {len(songs)} 首热门歌曲作为高评分歌曲替代")
        return songs
        
    except Exception as e:
        print(f"❌ get_high_rated_songs错误: {e}")
        import traceback
        traceback.print_exc()
        
        # 返回空列表
        return []


def get_song_by_id(song_id):
    """根据ID获取歌曲"""
    try:
        return Song.query.get(song_id)
    except Exception as e:
        print(f"获取歌曲错误: {e}")
        return None


def record_play(user_id, song_id):
    """记录播放历史"""
    try:
        # 更新歌曲播放计数
        song = Song.query.get(song_id)
        if song:
            song.play_count = (song.play_count or 0) + 1
            db.session.commit()
            
            # 记录播放历史
            history = PlayHistory.query.filter_by(
                user_id=user_id, 
                song_id=song_id
            ).first()
            
            if history:
                history.play_count += 1
                history.last_played = func.now()
            else:
                history = PlayHistory(
                    user_id=user_id,
                    song_id=song_id,
                    play_count=1,
                    last_played=func.now()
                )
                db.session.add(history)
            
            db.session.commit()
            return True
        return False
    except Exception as e:
        print(f"记录播放错误: {e}")
        db.session.rollback()
        return False


def search_songs(query, limit=20, offset=0):
    """搜索歌曲"""
    try:
        if not query or query.strip() == "":
            return Song.query.limit(limit).offset(offset).all()
        
        search_pattern = f"%{query}%"
        return Song.query.filter(
            or_(
                Song.title.ilike(search_pattern),
                Song.artist.ilike(search_pattern),
                Song.album.ilike(search_pattern),
                Song.genre.ilike(search_pattern)
            )
        ).limit(limit).offset(offset).all()
    except Exception as e:
        print(f"搜索歌曲错误: {e}")
        return []


def get_user_ratings(user_id, limit=20):
    """获取用户评分"""
    try:
        return Rating.query.filter_by(user_id=user_id).order_by(
            Rating.created_at.desc()
        ).limit(limit).all()
    except Exception as e:
        print(f"获取用户评分错误: {e}")
        return []


def get_user_play_history(user_id, limit=20):
    """获取用户播放历史"""
    try:
        return PlayHistory.query.filter_by(user_id=user_id).order_by(
            PlayHistory.last_played.desc()
        ).limit(limit).all()
    except Exception as e:
        print(f"获取播放历史错误: {e}")
        return []


def get_similar_songs(song_id, limit=5):
    """获取相似歌曲（基于相同艺术家或流派）"""
    try:
        song = Song.query.get(song_id)
        if not song:
            return []
        
        # 获取相同艺术家或流派的歌曲，排除当前歌曲
        similar = Song.query.filter(
            Song.id != song_id,
            or_(
                Song.artist == song.artist,
                Song.genre == song.genre
            )
        ).limit(limit).all()
        
        return similar
    except Exception as e:
        print(f"获取相似歌曲错误: {e}")
        return []


def update_song_rating(song_id):
    """更新歌曲的平均评分"""
    try:
        # 获取该歌曲的所有评分
        ratings = Rating.query.filter_by(song_id=song_id).all()
        
        if not ratings:
            # 如果没有评分，将平均评分设为0
            song = Song.query.get(song_id)
            if song:
                song.avg_rating = 0.0
                song.rating_count = 0
                db.session.commit()
            return
        
        # 计算平均分
        total = sum(r.rating for r in ratings)
        avg_rating = total / len(ratings)
        
        # 更新歌曲
        song = Song.query.get(song_id)
        if song:
            song.avg_rating = round(avg_rating, 1)
            song.rating_count = len(ratings)
            db.session.commit()
            
    except Exception as e:
        print(f"更新评分错误: {e}")
        db.session.rollback()


def create_user(username, email, password):
    """创建新用户"""
    try:
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return None, "用户名已存在"
        
        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            return None, "邮箱已存在"
        
        hashed_password = generate_password_hash(password)
        user = User(
            username=username,
            email=email,
            password_hash=hashed_password
        )
        
        db.session.add(user)
        db.session.commit()
        
        return user, "注册成功"
    except Exception as e:
        db.session.rollback()
        print(f"创建用户错误: {e}")
        return None, f"注册失败: {str(e)}"


def authenticate_user(username, password):
    """验证用户"""
    try:
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            return user
        return None
    except Exception as e:
        print(f"验证用户错误: {e}")
        return None


def get_similar_users(user_id, limit=5):
    """获取相似用户（基于评分相似度）"""
    try:
        # 获取当前用户的评分
        current_ratings = Rating.query.filter_by(user_id=user_id).all()
        if not current_ratings:
            return []
        
        # 获取所有其他用户
        all_users = User.query.filter(User.id != user_id).all()
        similar_users = []
        
        for user in all_users:
            user_ratings = Rating.query.filter_by(user_id=user.id).all()
            if not user_ratings:
                continue
            
            # 计算评分相似度
            common_songs = 0
            rating_diff_sum = 0
            
            for rating1 in current_ratings:
                for rating2 in user_ratings:
                    if rating1.song_id == rating2.song_id:
                        common_songs += 1
                        rating_diff_sum += abs(rating1.rating - rating2.rating)
            
            if common_songs > 0:
                avg_diff = rating_diff_sum / common_songs
                similarity = max(0, 5 - avg_diff) / 5  # 归一化到0-1
                
                if similarity > 0.3:
                    similar_users.append({
                        'user': user,
                        'similarity': similarity,
                        'common_songs': common_songs
                    })
        
        # 按相似度排序
        similar_users.sort(key=lambda x: x['similarity'], reverse=True)
        return similar_users[:limit]
    except Exception as e:
        print(f"获取相似用户错误: {e}")
        return []


def update_all_song_ratings():
    """更新所有歌曲的评分统计"""
    try:
        songs = Song.query.all()
        updated_count = 0
        
        for song in songs:
            # 获取该歌曲的所有评分
            ratings = Rating.query.filter_by(song_id=song.id).all()
            
            if ratings:
                # 计算平均分
                total = sum(r.rating for r in ratings)
                avg_rating = total / len(ratings)
                
                # 更新歌曲
                song.avg_rating = round(avg_rating, 1)
                song.rating_count = len(ratings)
                updated_count += 1
            else:
                # 如果没有评分
                song.avg_rating = 0.0
                song.rating_count = 0
        
        db.session.commit()
        print(f"✅ 已更新{updated_count}首歌曲的评分统计")
        return updated_count
        
    except Exception as e:
        db.session.rollback()
        print(f"更新评分统计错误: {e}")
        return 0