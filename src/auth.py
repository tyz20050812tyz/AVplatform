#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户认证模块
提供登录、注册、会话管理功能
"""

try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False
    # 为测试环境创建mock对象
    class MockStreamlit:
        def __init__(self):
            self.session_state = {}
        def markdown(self, *args, **kwargs): pass
        def form(self, *args, **kwargs): return self
        def columns(self, *args, **kwargs): return [self, self, self]
        def text_input(self, *args, **kwargs): return ""
        def form_submit_button(self, *args, **kwargs): return False
        def error(self, *args, **kwargs): pass
        def success(self, *args, **kwargs): pass
        def info(self, *args, **kwargs): pass
        def rerun(self): pass
        def expander(self, *args, **kwargs): return self
        def button(self, *args, **kwargs): return False
        def sidebar(self): return self
        def write(self, *args, **kwargs): pass
        def __enter__(self): return self
        def __exit__(self, *args): pass
    
    st = MockStreamlit()

import sqlite3
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import re

# 配置常量
SESSION_TIMEOUT_HOURS = 24  # 会话超时时间（小时）
MIN_PASSWORD_LENGTH = 6  # 最小密码长度
MAX_LOGIN_ATTEMPTS = 5  # 最大登录尝试次数

def init_auth_database():
    """初始化用户认证数据库"""
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    
    # 创建用户表
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            created_at TEXT NOT NULL,
            last_login TEXT,
            is_active INTEGER DEFAULT 1,
            failed_login_attempts INTEGER DEFAULT 0,
            locked_until TEXT
        )
    ''')
    
    # 创建会话表
    c.execute('''
        CREATE TABLE IF NOT EXISTS user_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            session_token TEXT UNIQUE NOT NULL,
            created_at TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            is_active INTEGER DEFAULT 1,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # 创建默认管理员账户
    c.execute("SELECT COUNT(*) FROM users WHERE username = 'admin'")
    if c.fetchone()[0] == 0:
        admin_salt = secrets.token_hex(32)
        admin_password_hash = hash_password("admin123", admin_salt)
        
        c.execute('''
            INSERT INTO users (username, email, password_hash, salt, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            'admin',
            'admin@platform.com',
            admin_password_hash,
            admin_salt,
            datetime.now().isoformat()
        ))
    
    conn.commit()
    conn.close()

def hash_password(password: str, salt: str) -> str:
    """对密码进行哈希处理"""
    return hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000).hex()

def validate_email(email: str) -> bool:
    """验证邮箱格式"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_username(username: str) -> bool:
    """验证用户名格式"""
    if len(username) < 3 or len(username) > 20:
        return False
    pattern = r'^[a-zA-Z0-9_]+$'
    return re.match(pattern, username) is not None

def validate_password(password: str) -> tuple[bool, str]:
    """验证密码强度"""
    if len(password) < MIN_PASSWORD_LENGTH:
        return False, f"密码长度至少为 {MIN_PASSWORD_LENGTH} 位"
    
    if not re.search(r'[A-Za-z]', password):
        return False, "密码必须包含字母"
    
    if not re.search(r'[0-9]', password):
        return False, "密码必须包含数字"
    
    return True, "密码强度合格"

def is_user_locked(username: str) -> tuple[bool, Optional[str]]:
    """检查用户是否被锁定"""
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    
    c.execute('''
        SELECT failed_login_attempts, locked_until 
        FROM users 
        WHERE username = ?
    ''', (username,))
    
    result = c.fetchone()
    conn.close()
    
    if not result:
        return False, None
    
    failed_attempts, locked_until = result
    
    if locked_until:
        lock_time = datetime.fromisoformat(locked_until)
        if datetime.now() < lock_time:
            return True, locked_until
        else:
            # 锁定时间已过，清除锁定状态
            clear_user_lock(username)
    
    return False, None

def clear_user_lock(username: str):
    """清除用户锁定状态"""
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    
    c.execute('''
        UPDATE users 
        SET failed_login_attempts = 0, locked_until = NULL 
        WHERE username = ?
    ''', (username,))
    
    conn.commit()
    conn.close()

def increment_failed_login(username: str):
    """增加登录失败次数"""
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    
    c.execute('''
        UPDATE users 
        SET failed_login_attempts = failed_login_attempts + 1 
        WHERE username = ?
    ''', (username,))
    
    # 检查是否需要锁定账户
    c.execute('''
        SELECT failed_login_attempts 
        FROM users 
        WHERE username = ?
    ''', (username,))
    
    result = c.fetchone()
    if result and result[0] >= MAX_LOGIN_ATTEMPTS:
        # 锁定账户1小时
        lock_until = datetime.now() + timedelta(hours=1)
        c.execute('''
            UPDATE users 
            SET locked_until = ? 
            WHERE username = ?
        ''', (lock_until.isoformat(), username))
    
    conn.commit()
    conn.close()

def authenticate_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    """验证用户登录"""
    # 检查用户是否被锁定
    is_locked, locked_until = is_user_locked(username)
    if is_locked:
        return None
    
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    
    c.execute('''
        SELECT id, username, email, password_hash, salt, is_active
        FROM users 
        WHERE username = ? AND is_active = 1
    ''', (username,))
    
    user = c.fetchone()
    conn.close()
    
    if not user:
        return None
    
    user_id, username, email, stored_hash, salt, is_active = user
    
    # 验证密码
    password_hash = hash_password(password, salt)
    if password_hash == stored_hash:
        # 登录成功，清除失败次数
        clear_user_lock(username)
        
        # 更新最后登录时间
        conn = sqlite3.connect('data.db')
        c = conn.cursor()
        c.execute('''
            UPDATE users 
            SET last_login = ? 
            WHERE id = ?
        ''', (datetime.now().isoformat(), user_id))
        conn.commit()
        conn.close()
        
        return {
            'id': user_id,
            'username': username,
            'email': email
        }
    else:
        # 登录失败，增加失败次数
        increment_failed_login(username)
        return None

def create_user_session(user_id: int) -> str:
    """创建用户会话"""
    session_token = secrets.token_urlsafe(32)
    expires_at = datetime.now() + timedelta(hours=SESSION_TIMEOUT_HOURS)
    
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    
    # 清除该用户的旧会话
    c.execute('''
        UPDATE user_sessions 
        SET is_active = 0 
        WHERE user_id = ?
    ''', (user_id,))
    
    # 创建新会话
    c.execute('''
        INSERT INTO user_sessions (user_id, session_token, created_at, expires_at)
        VALUES (?, ?, ?, ?)
    ''', (
        user_id,
        session_token,
        datetime.now().isoformat(),
        expires_at.isoformat()
    ))
    
    conn.commit()
    conn.close()
    
    return session_token

def verify_session(session_token: str) -> Optional[Dict[str, Any]]:
    """验证会话有效性"""
    if not session_token:
        return None
    
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    
    c.execute('''
        SELECT u.id, u.username, u.email, s.expires_at
        FROM user_sessions s
        JOIN users u ON s.user_id = u.id
        WHERE s.session_token = ? AND s.is_active = 1 AND u.is_active = 1
    ''', (session_token,))
    
    result = c.fetchone()
    conn.close()
    
    if not result:
        return None
    
    user_id, username, email, expires_at = result
    
    # 检查会话是否过期
    if datetime.now() > datetime.fromisoformat(expires_at):
        invalidate_session(session_token)
        return None
    
    return {
        'id': user_id,
        'username': username,
        'email': email
    }

def invalidate_session(session_token: str):
    """使会话失效"""
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    
    c.execute('''
        UPDATE user_sessions 
        SET is_active = 0 
        WHERE session_token = ?
    ''', (session_token,))
    
    conn.commit()
    conn.close()

def register_user(username: str, email: str, password: str) -> tuple[bool, str]:
    """注册新用户"""
    # 验证输入
    if not validate_username(username):
        return False, "用户名格式不正确（3-20位字母数字下划线）"
    
    if not validate_email(email):
        return False, "邮箱格式不正确"
    
    is_valid, password_msg = validate_password(password)
    if not is_valid:
        return False, password_msg
    
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    
    # 检查用户名是否已存在
    c.execute("SELECT id FROM users WHERE username = ?", (username,))
    if c.fetchone():
        conn.close()
        return False, "用户名已存在"
    
    # 检查邮箱是否已存在
    c.execute("SELECT id FROM users WHERE email = ?", (email,))
    if c.fetchone():
        conn.close()
        return False, "邮箱已被注册"
    
    # 创建新用户
    try:
        salt = secrets.token_hex(32)
        password_hash = hash_password(password, salt)
        
        c.execute('''
            INSERT INTO users (username, email, password_hash, salt, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            username,
            email,
            password_hash,
            salt,
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
        return True, "注册成功"
        
    except Exception as e:
        conn.close()
        return False, f"注册失败: {str(e)}"

def show_login_page():
    """显示登录页面"""
    st.markdown("""
    <div style="text-align: center; padding: 2rem 0;">
        <h1>🚗 无人驾驶数据管理平台</h1>
        <h3>用户登录</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # 登录表单
    with st.form("login_form"):
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.markdown("### 📝 登录信息")
            username = st.text_input("👤 用户名", placeholder="请输入用户名")
            password = st.text_input("🔒 密码", type="password", placeholder="请输入密码")
            
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                login_clicked = st.form_submit_button("🔑 登录", type="primary", use_container_width=True)
            with col_btn2:
                register_clicked = st.form_submit_button("📝 注册", use_container_width=True)
    
    # 处理登录
    if login_clicked:
        if not username or not password:
            st.error("❌ 请输入用户名和密码")
        else:
            # 检查用户是否被锁定
            is_locked, locked_until = is_user_locked(username)
            if is_locked:
                lock_time = datetime.fromisoformat(locked_until)
                remaining_time = lock_time - datetime.now()
                minutes = int(remaining_time.total_seconds() / 60)
                st.error(f"🔒 账户已被锁定，请在 {minutes} 分钟后重试")
            else:
                user = authenticate_user(username, password)
                if user:
                    # 创建会话
                    session_token = create_user_session(user['id'])
                    
                    # 保存到session state
                    st.session_state.user = user
                    st.session_state.session_token = session_token
                    st.session_state.authenticated = True
                    
                    st.success(f"✅ 登录成功！欢迎回来，{user['username']}")
                    st.rerun()
                else:
                    st.error("❌ 用户名或密码错误")
    
    # 处理注册
    if register_clicked:
        st.session_state.show_register = True
        st.rerun()
    
    # 显示默认账户信息
    with st.expander("💡 测试账户信息"):
        st.info("""
        **默认管理员账户：**
        - 用户名：admin
        - 密码：admin123
        
        **注意：** 首次使用建议修改默认密码
        """)

def show_register_page():
    """显示注册页面"""
    st.markdown("""
    <div style="text-align: center; padding: 2rem 0;">
        <h1>🚗 无人驾驶数据管理平台</h1>
        <h3>用户注册</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # 注册表单
    with st.form("register_form"):
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.markdown("### 📝 注册信息")
            username = st.text_input("👤 用户名", placeholder="3-20位字母数字下划线", help="用户名只能包含字母、数字和下划线")
            email = st.text_input("📧 邮箱", placeholder="请输入邮箱地址")
            password = st.text_input("🔒 密码", type="password", placeholder="至少6位，包含字母和数字")
            password_confirm = st.text_input("🔒 确认密码", type="password", placeholder="请再次输入密码")
            
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                register_clicked = st.form_submit_button("📝 注册", type="primary", use_container_width=True)
            with col_btn2:
                back_clicked = st.form_submit_button("🔙 返回登录", use_container_width=True)
    
    # 处理注册
    if register_clicked:
        if not username or not email or not password or not password_confirm:
            st.error("❌ 请填写完整信息")
        elif password != password_confirm:
            st.error("❌ 两次输入的密码不一致")
        else:
            success, message = register_user(username, email, password)
            if success:
                st.success(f"✅ {message}")
                st.info("🔑 请使用新账户登录")
                st.session_state.show_register = False
                st.rerun()
            else:
                st.error(f"❌ {message}")
    
    # 返回登录
    if back_clicked:
        st.session_state.show_register = False
        st.rerun()

def show_user_info():
    """显示用户信息"""
    if 'user' in st.session_state:
        user = st.session_state.user
        
        with st.sidebar:
            st.markdown("---")
            st.markdown("### 👤 用户信息")
            st.write(f"**用户名:** {user['username']}")
            st.write(f"**邮箱:** {user['email']}")
            
            if st.button("🚪 退出登录", use_container_width=True):
                logout_user()

def logout_user():
    """用户退出登录"""
    if 'session_token' in st.session_state:
        invalidate_session(st.session_state.session_token)
    
    # 清除session state
    for key in ['user', 'session_token', 'authenticated']:
        if key in st.session_state:
            del st.session_state[key]
    
    st.rerun()

def check_authentication() -> bool:
    """检查用户认证状态"""
    # 检查session state
    if 'authenticated' in st.session_state and st.session_state.authenticated:
        # 验证session token
        if 'session_token' in st.session_state:
            user = verify_session(st.session_state.session_token)
            if user:
                st.session_state.user = user
                return True
            else:
                # session失效，清除状态
                logout_user()
    
    return False

def require_authentication():
    """装饰器：要求用户认证"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            if check_authentication():
                return func(*args, **kwargs)
            else:
                show_auth_page()
        return wrapper
    return decorator

def show_auth_page():
    """显示认证页面"""
    # 初始化认证数据库
    init_auth_database()
    
    # 根据状态显示不同页面
    if st.session_state.get('show_register', False):
        show_register_page()
    else:
        show_login_page()