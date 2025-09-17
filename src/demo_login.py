#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
登录功能演示脚本
在命令行中演示用户认证流程
"""

import os
import sys
from getpass import getpass

# 添加当前目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def demo_login_system():
    """演示登录系统"""
    print("=" * 60)
    print("🚗 无人驾驶数据管理平台 - 登录系统演示")
    print("=" * 60)
    
    try:
        from auth import (
            init_auth_database,
            authenticate_user,
            register_user,
            create_user_session,
            verify_session
        )
        
        # 初始化数据库
        init_auth_database()
        print("✅ 数据库初始化完成")
        
        while True:
            print("\n📋 请选择操作:")
            print("1. 👤 用户登录")
            print("2. 📝 用户注册") 
            print("3. 🔍 查看用户列表")
            print("4. 🚪 退出系统")
            
            choice = input("\n请输入选择 (1-4): ").strip()
            
            if choice == "1":
                # 用户登录
                print("\n🔑 用户登录")
                username = input("👤 用户名: ").strip()
                password = getpass("🔒 密码: ")
                
                if not username or not password:
                    print("❌ 请输入完整的用户名和密码")
                    continue
                
                user = authenticate_user(username, password)
                if user:
                    print(f"\n✅ 登录成功！")
                    print(f"   欢迎回来，{user['username']} ({user['email']})")
                    
                    # 创建会话
                    session_token = create_user_session(user['id'])
                    print(f"   会话令牌: {session_token[:20]}...")
                    
                    # 验证会话
                    session_user = verify_session(session_token)
                    if session_user:
                        print("   ✅ 会话验证成功")
                    
                    # 模拟登录后的操作
                    print("\n🎯 登录后可用功能:")
                    print("   - 📤 数据上传")
                    print("   - 📁 数据浏览") 
                    print("   - 📈 数据可视化")
                    print("   - 🌌 点云数据处理")
                    
                else:
                    print("❌ 登录失败：用户名或密码错误")
            
            elif choice == "2":
                # 用户注册
                print("\n📝 用户注册")
                username = input("👤 用户名 (3-20位字母数字下划线): ").strip()
                email = input("📧 邮箱地址: ").strip()
                password = getpass("🔒 密码 (至少6位，包含字母和数字): ")
                password_confirm = getpass("🔒 确认密码: ")
                
                if not all([username, email, password, password_confirm]):
                    print("❌ 请填写完整信息")
                    continue
                
                if password != password_confirm:
                    print("❌ 两次输入的密码不一致")
                    continue
                
                success, message = register_user(username, email, password)
                if success:
                    print(f"✅ {message}")
                    print("💡 请使用新账户登录")
                else:
                    print(f"❌ {message}")
            
            elif choice == "3":
                # 查看用户列表
                print("\n👥 用户列表")
                try:
                    import sqlite3
                    from datetime import datetime
                    
                    conn = sqlite3.connect('data.db')
                    c = conn.cursor()
                    c.execute("""
                        SELECT username, email, created_at, last_login 
                        FROM users 
                        ORDER BY created_at DESC
                    """)
                    users = c.fetchall()
                    conn.close()
                    
                    if users:
                        print(f"{'用户名':<15} {'邮箱':<25} {'注册时间':<20} {'最后登录':<20}")
                        print("-" * 80)
                        for username, email, created_at, last_login in users:
                            created_time = datetime.fromisoformat(created_at).strftime('%Y-%m-%d %H:%M:%S')
                            last_login_time = "从未登录"
                            if last_login:
                                last_login_time = datetime.fromisoformat(last_login).strftime('%Y-%m-%d %H:%M:%S')
                            
                            print(f"{username:<15} {email:<25} {created_time:<20} {last_login_time:<20}")
                    else:
                        print("   暂无用户")
                        
                except Exception as e:
                    print(f"❌ 查询用户列表失败: {e}")
            
            elif choice == "4":
                print("\n👋 感谢使用无人驾驶数据管理平台！")
                break
            
            else:
                print("❌ 无效选择，请输入 1-4")
        
    except ImportError as e:
        print(f"❌ 导入模块失败: {e}")
    except Exception as e:
        print(f"❌ 系统错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    demo_login_system()