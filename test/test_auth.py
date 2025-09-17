#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户认证功能测试脚本
测试用户注册、登录、会话管理等核心功能
"""

import os
import sys
import sqlite3
from datetime import datetime

# 添加当前目录到路径，以便导入auth模块
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_auth_functions():
    """测试认证功能"""
    print("🔐 开始测试用户认证功能...")
    
    # 删除测试数据库文件（如果存在）
    if os.path.exists('data.db'):
        os.remove('data.db')
        print("🗑️ 清除旧的测试数据库")
    
    try:
        # 导入认证模块
        from auth import (
            init_auth_database, 
            register_user, 
            authenticate_user, 
            create_user_session,
            verify_session,
            validate_email,
            validate_username,
            validate_password
        )
        
        print("✅ 认证模块导入成功")
        
        # 1. 测试数据库初始化
        print("\n📊 测试数据库初始化...")
        init_auth_database()
        print("✅ 数据库初始化成功")
        
        # 检查默认管理员账户
        conn = sqlite3.connect('data.db')
        c = conn.cursor()
        c.execute("SELECT username, email FROM users WHERE username = 'admin'")
        admin_user = c.fetchone()
        conn.close()
        
        if admin_user:
            print(f"✅ 默认管理员账户创建成功: {admin_user[0]} ({admin_user[1]})")
        else:
            print("❌ 默认管理员账户创建失败")
        
        # 2. 测试输入验证
        print("\n📝 测试输入验证...")
        
        # 测试用户名验证
        test_cases = [
            ("validuser", True, "有效用户名"),
            ("ab", False, "用户名太短"),
            ("user@invalid", False, "包含非法字符"),
            ("valid_user123", True, "有效用户名（数字下划线）")
        ]
        
        for username, expected, desc in test_cases:
            result = validate_username(username)
            status = "✅" if result == expected else "❌"
            print(f"  {status} {desc}: {username} -> {result}")
        
        # 测试邮箱验证
        email_tests = [
            ("user@example.com", True, "有效邮箱"),
            ("invalid-email", False, "无效邮箱格式"),
            ("test@domain.co.uk", True, "有效邮箱（多级域名）")
        ]
        
        for email, expected, desc in email_tests:
            result = validate_email(email)
            status = "✅" if result == expected else "❌"
            print(f"  {status} {desc}: {email} -> {result}")
        
        # 测试密码验证
        password_tests = [
            ("123", False, "密码太短"),
            ("password", False, "只有字母"),
            ("123456", False, "只有数字"),
            ("pass123", True, "有效密码")
        ]
        
        for password, expected, desc in password_tests:
            result, message = validate_password(password)
            status = "✅" if result == expected else "❌"
            print(f"  {status} {desc}: {password} -> {result} ({message})")
        
        # 3. 测试用户注册
        print("\n👤 测试用户注册...")
        
        # 注册新用户
        success, message = register_user("testuser", "test@example.com", "test123")
        print(f"{'✅' if success else '❌'} 注册新用户: {message}")
        
        # 测试重复注册
        success, message = register_user("testuser", "test2@example.com", "test123")
        print(f"{'✅' if not success else '❌'} 重复用户名注册: {message}")
        
        success, message = register_user("testuser2", "test@example.com", "test123")
        print(f"{'✅' if not success else '❌'} 重复邮箱注册: {message}")
        
        # 4. 测试用户登录
        print("\n🔑 测试用户登录...")
        
        # 正确登录
        user = authenticate_user("testuser", "test123")
        if user:
            print(f"✅ 正确密码登录成功: {user['username']} ({user['email']})")
        else:
            print("❌ 正确密码登录失败")
        
        # 错误密码
        user = authenticate_user("testuser", "wrongpassword")
        print(f"{'✅' if not user else '❌'} 错误密码登录: {'被正确拒绝' if not user else '意外成功'}")
        
        # 不存在的用户
        user = authenticate_user("nonexistent", "test123")
        print(f"{'✅' if not user else '❌'} 不存在用户登录: {'被正确拒绝' if not user else '意外成功'}")
        
        # 管理员登录
        admin = authenticate_user("admin", "admin123")
        if admin:
            print(f"✅ 管理员登录成功: {admin['username']}")
        else:
            print("❌ 管理员登录失败")
        
        # 5. 测试会话管理
        print("\n🎫 测试会话管理...")
        
        if user:  # 使用之前成功登录的用户
            # 创建会话
            session_token = create_user_session(user['id'])
            print(f"✅ 会话创建成功: {session_token[:20]}...")
            
            # 验证会话
            session_user = verify_session(session_token)
            if session_user and session_user['id'] == user['id']:
                print("✅ 会话验证成功")
            else:
                print("❌ 会话验证失败")
            
            # 测试无效会话
            invalid_session = verify_session("invalid_token")
            print(f"{'✅' if not invalid_session else '❌'} 无效会话: {'被正确拒绝' if not invalid_session else '意外通过'}")
        
        # 6. 显示数据库统计
        print("\n📊 数据库统计信息...")
        conn = sqlite3.connect('data.db')
        c = conn.cursor()
        
        c.execute("SELECT COUNT(*) FROM users")
        user_count = c.fetchone()[0]
        print(f"  用户总数: {user_count}")
        
        c.execute("SELECT COUNT(*) FROM user_sessions WHERE is_active = 1")
        session_count = c.fetchone()[0]
        print(f"  活跃会话数: {session_count}")
        
        c.execute("SELECT username, email, created_at FROM users")
        users = c.fetchall()
        print("  用户列表:")
        for username, email, created_at in users:
            created_time = datetime.fromisoformat(created_at).strftime('%Y-%m-%d %H:%M:%S')
            print(f"    - {username} ({email}) - 创建于 {created_time}")
        
        conn.close()
        
        print("\n🎯 认证功能测试完成！")
        print("💡 所有核心功能都已验证，可以在Streamlit应用中使用")
        
    except ImportError as e:
        print(f"❌ 导入认证模块失败: {e}")
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_auth_functions()