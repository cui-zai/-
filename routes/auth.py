"""
认证路由
"""
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from database.db_operations import create_user, authenticate_user, get_user_by_username
from utils.validators import validate_username, validate_email, validate_password

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """登录页面"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember = request.form.get('remember', False)
        
        # 验证输入
        if not username or not password:
            flash('用户名和密码不能为空', 'danger')
            return render_template('login.html')
        
        # 验证用户
        user = authenticate_user(username, password)
        if user:
            login_user(user, remember=remember)
            flash('登录成功！', 'success')
            
            # 重定向到来源页面或首页
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            flash('用户名或密码错误', 'danger')
    
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """注册页面"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        age = request.form.get('age')
        gender = request.form.get('gender')
        location = request.form.get('location', '').strip()
        
        # 验证输入
        errors = []
        
        # 验证用户名
        is_valid_username, username_msg = validate_username(username)
        if not is_valid_username:
            errors.append(username_msg)
        
        # 验证邮箱
        is_valid_email, email_msg = validate_email(email)
        if not is_valid_email:
            errors.append(email_msg)
        
        # 验证密码
        is_valid_password, password_msg = validate_password(password)
        if not is_valid_password:
            errors.append(password_msg)
        
        # 确认密码
        if password != confirm_password:
            errors.append('两次输入的密码不一致')
        
        # 验证年龄
        if age:
            try:
                age = int(age)
                if age < 0 or age > 150:
                    errors.append('年龄必须在0-150之间')
            except ValueError:
                errors.append('年龄必须是数字')
        
        # 如果有错误，显示错误信息
        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('register.html')
        
        try:
            # 创建用户
            user = create_user(
                username=username,
                email=email,
                password=password,
                age=int(age) if age else None,
                gender=gender if gender else None,
                location=location if location else None
            )
            
            # 自动登录
            login_user(user)
            flash('注册成功！欢迎使用音乐推荐系统', 'success')
            return redirect(url_for('index'))
            
        except ValueError as e:
            flash(str(e), 'danger')
        except Exception as e:
            flash('注册失败，请稍后重试', 'danger')
    
    return render_template('register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """退出登录"""
    logout_user()
    flash('已成功退出登录', 'info')
    return redirect(url_for('index'))

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """个人资料页面"""
    if request.method == 'POST':
        # 更新用户资料
        email = request.form.get('email', '').strip()
        age = request.form.get('age')
        gender = request.form.get('gender')
        location = request.form.get('location', '').strip()
        
        # 验证邮箱
        is_valid_email, email_msg = validate_email(email)
        if not is_valid_email:
            flash(email_msg, 'danger')
            return redirect(url_for('auth.profile'))
        
        # 验证年龄
        if age:
            try:
                age = int(age)
                if age < 0 or age > 150:
                    flash('年龄必须在0-150之间', 'danger')
                    return redirect(url_for('auth.profile'))
            except ValueError:
                flash('年龄必须是数字', 'danger')
                return redirect(url_for('auth.profile'))
        
        # 更新用户信息
        current_user.email = email
        current_user.age = int(age) if age else None
        current_user.gender = gender if gender else None
        current_user.location = location if location else None
        
        from database.models import db
        db.session.commit()
        
        flash('个人资料更新成功', 'success')
        return redirect(url_for('auth.profile'))
    
    return render_template('profile.html')

@auth_bp.route('/change_password', methods=['POST'])
@login_required
def change_password():
    """修改密码"""
    current_password = request.form.get('current_password', '')
    new_password = request.form.get('new_password', '')
    confirm_password = request.form.get('confirm_password', '')
    
    # 验证当前密码
    if not current_user.check_password(current_password):
        flash('当前密码错误', 'danger')
        return redirect(url_for('auth.profile'))
    
    # 验证新密码
    is_valid_password, password_msg = validate_password(new_password)
    if not is_valid_password:
        flash(password_msg, 'danger')
        return redirect(url_for('auth.profile'))
    
    # 确认密码
    if new_password != confirm_password:
        flash('两次输入的新密码不一致', 'danger')
        return redirect(url_for('auth.profile'))
    
    # 更新密码
    current_user.set_password(new_password)
    
    from database.models import db
    db.session.commit()
    
    flash('密码修改成功', 'success')
    return redirect(url_for('auth.profile'))

@auth_bp.route('/check_username/<username>')
def check_username(username):
    """检查用户名是否可用"""
    user = get_user_by_username(username)
    is_available = user is None
    
    return jsonify({
        'available': is_available,
        'username': username
    })

@auth_bp.route('/check_email/<email>')
def check_email(email):
    """检查邮箱是否可用"""
    from database.db_operations import get_user_by_email
    user = get_user_by_email(email)
    is_available = user is None
    
    return jsonify({
        'available': is_available,
        'email': email
    })