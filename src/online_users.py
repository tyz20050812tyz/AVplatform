#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
在线用户统计模块
实时跟踪网站在线人数
"""

import sqlite3
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import json
import os

# 配置常量
ONLINE_TIMEOUT_MINUTES = 5  # 用户超时时间（分钟）
HEARTBEAT_INTERVAL = 30  # 心跳间隔（秒）

class OnlineUserManager:
    """在线用户管理器"""
    
    def __init__(self, db_path='data.db'):
        self.db_path = db_path
        self.init_online_users_table()
    
    def init_online_users_table(self):
        """初始化在线用户表"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # 创建在线用户表
        c.execute('''
            CREATE TABLE IF NOT EXISTS online_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE NOT NULL,
                username TEXT,
                ip_address TEXT,
                user_agent TEXT,
                login_time TEXT NOT NULL,
                last_seen TEXT NOT NULL,
                page_path TEXT,
                is_active INTEGER DEFAULT 1
            )
        ''')
        
        # 创建访问日志表
        c.execute('''
            CREATE TABLE IF NOT EXISTS user_visits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                username TEXT,
                ip_address TEXT,
                visit_time TEXT NOT NULL,
                page_path TEXT,
                action TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_online_user(self, session_id: str, username: Optional[str] = None, 
                       ip_address: Optional[str] = None, user_agent: Optional[str] = None,
                       page_path: Optional[str] = None):
        """添加在线用户"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        current_time = datetime.now().isoformat()
        
        # 使用 INSERT OR REPLACE 来处理重复的 session_id
        c.execute('''
            INSERT OR REPLACE INTO online_users 
            (session_id, username, ip_address, user_agent, login_time, last_seen, page_path, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, 1)
        ''', (session_id, username, ip_address, user_agent, current_time, current_time, page_path))
        
        # 记录访问日志
        c.execute('''
            INSERT INTO user_visits (session_id, username, ip_address, visit_time, page_path, action)
            VALUES (?, ?, ?, ?, ?, 'login')
        ''', (session_id, username, ip_address, current_time, page_path))
        
        conn.commit()
        conn.close()
    
    def update_user_activity(self, session_id: str, page_path: Optional[str] = None):
        """更新用户活动状态"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        current_time = datetime.now().isoformat()
        
        if page_path:
            c.execute('''
                UPDATE online_users 
                SET last_seen = ?, page_path = ?, is_active = 1
                WHERE session_id = ?
            ''', (current_time, page_path, session_id))
        else:
            c.execute('''
                UPDATE online_users 
                SET last_seen = ?, is_active = 1
                WHERE session_id = ?
            ''', (current_time, session_id))
        
        conn.commit()
        conn.close()
    
    def remove_user(self, session_id: str):
        """移除用户（登出）"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # 记录登出日志
        current_time = datetime.now().isoformat()
        c.execute('''
            INSERT INTO user_visits (session_id, visit_time, action)
            SELECT session_id, ?, 'logout' FROM online_users WHERE session_id = ?
        ''', (current_time, session_id))
        
        # 删除在线用户记录
        c.execute('DELETE FROM online_users WHERE session_id = ?', (session_id,))
        
        conn.commit()
        conn.close()
    
    def cleanup_inactive_users(self):
        """清理不活跃用户"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # 计算超时时间
        timeout_time = datetime.now() - timedelta(minutes=ONLINE_TIMEOUT_MINUTES)
        timeout_str = timeout_time.isoformat()
        
        # 删除超时用户
        c.execute('DELETE FROM online_users WHERE last_seen < ?', (timeout_str,))
        
        conn.commit()
        conn.close()
    
    def get_online_count(self) -> int:
        """获取在线用户数"""
        # 先清理不活跃用户
        self.cleanup_inactive_users()
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('SELECT COUNT(*) FROM online_users WHERE is_active = 1')
        count = c.fetchone()[0]
        
        conn.close()
        return count
    
    def get_online_users(self) -> list:
        """获取在线用户列表"""
        # 先清理不活跃用户
        self.cleanup_inactive_users()
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''
            SELECT session_id, username, ip_address, login_time, last_seen, page_path
            FROM online_users 
            WHERE is_active = 1
            ORDER BY last_seen DESC
        ''')
        
        users = []
        for row in c.fetchall():
            users.append({
                'session_id': row[0],
                'username': row[1] or '游客',
                'ip_address': row[2],
                'login_time': row[3],
                'last_seen': row[4],
                'page_path': row[5],
                'online_duration': self._calculate_duration(row[3])
            })
        
        conn.close()
        return users
    
    def _calculate_duration(self, login_time_str: str) -> str:
        """计算在线时长"""
        try:
            login_time = datetime.fromisoformat(login_time_str)
            duration = datetime.now() - login_time
            
            hours = int(duration.total_seconds() // 3600)
            minutes = int((duration.total_seconds() % 3600) // 60)
            
            if hours > 0:
                return f"{hours}小时{minutes}分钟"
            else:
                return f"{minutes}分钟"
        except:
            return "未知"
    
    def get_visit_stats(self) -> Dict[str, Any]:
        """获取访问统计"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # 今日访问量
        today = datetime.now().strftime('%Y-%m-%d')
        c.execute('''
            SELECT COUNT(DISTINCT session_id) 
            FROM user_visits 
            WHERE visit_time LIKE ? AND action = 'login'
        ''', (f"{today}%",))
        today_visits = c.fetchone()[0]
        
        # 总访问量
        c.execute('SELECT COUNT(DISTINCT session_id) FROM user_visits WHERE action = "login"')
        total_visits = c.fetchone()[0]
        
        # 当前在线人数
        online_count = self.get_online_count()
        
        conn.close()
        
        return {
            'online_count': online_count,
            'today_visits': today_visits,
            'total_visits': total_visits
        }

# 全局在线用户管理器实例
online_manager = OnlineUserManager()

def track_user_online(session_id: str, username: Optional[str] = None, 
                     page_path: Optional[str] = None):
    """跟踪用户在线状态（便捷函数）"""
    # 从网络配置获取数据库路径
    try:
        from network_storage import network_config
        db_path = network_config.get_database_path()
        manager = OnlineUserManager(db_path)
    except:
        manager = online_manager
    
    manager.update_user_activity(session_id, page_path)

def get_online_users_count() -> int:
    """获取在线用户数（便捷函数）"""
    try:
        from network_storage import network_config
        db_path = network_config.get_database_path()
        manager = OnlineUserManager(db_path)
    except:
        manager = online_manager
    
    return manager.get_online_count()

def add_user_online(session_id: str, username: Optional[str] = None, 
                   ip_address: Optional[str] = None, page_path: Optional[str] = None):
    """添加在线用户（便捷函数）"""
    try:
        from network_storage import network_config
        db_path = network_config.get_database_path()
        manager = OnlineUserManager(db_path)
    except:
        manager = online_manager
    
    manager.add_online_user(session_id, username, ip_address, page_path=page_path)

def remove_user_online(session_id: str):
    """移除在线用户（便捷函数）"""
    try:
        from network_storage import network_config
        db_path = network_config.get_database_path()
        manager = OnlineUserManager(db_path)
    except:
        manager = online_manager
    
    manager.remove_user(session_id)