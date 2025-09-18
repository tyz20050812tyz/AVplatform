#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清理测试数据脚本
删除IP地址为"未知"的测试用户数据
"""

import sqlite3
import sys
import os

# 添加src路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

def clean_test_data():
    """清理测试数据"""
    print("🧹 开始清理所有测试数据...")
    
    try:
        # 连接数据库
        conn = sqlite3.connect('data.db')
        c = conn.cursor()
        
        # 查看清理前的数据
        print("\n📊 清理前的数据:")
        c.execute("SELECT COUNT(*) FROM online_users")
        before_count = c.fetchone()[0]
        print(f"  在线用户总数: {before_count}")
        
        # 显示所有用户
        c.execute("SELECT username, ip_address FROM online_users")
        all_users = c.fetchall()
        print("\n  当前用户列表:")
        for username, ip in all_users:
            print(f"    - {username}: {ip or '未知'}")
        
        # 清空所有在线用户数据
        c.execute("DELETE FROM online_users")
        deleted_online = c.rowcount
        
        # 清空所有访问日志
        c.execute("DELETE FROM user_visits")
        deleted_visits = c.rowcount
        
        # 重置自增ID
        c.execute("DELETE FROM sqlite_sequence WHERE name='online_users'")
        c.execute("DELETE FROM sqlite_sequence WHERE name='user_visits'")
        
        conn.commit()
        conn.close()
        
        print(f"\n✅ 清理完成:")
        print(f"  删除在线用户记录: {deleted_online} 条")
        print(f"  删除访问日志记录: {deleted_visits} 条")
        print(f"  剩余在线用户: 0 个")
        print("  ✅ 已重置数据库ID序列")
        
    except Exception as e:
        print(f"❌ 清理失败: {e}")

def show_current_users():
    """显示当前用户列表"""
    print("\n👥 当前在线用户:")
    
    try:
        conn = sqlite3.connect('data.db')
        c = conn.cursor()
        
        c.execute("""
            SELECT username, ip_address, login_time, page_path 
            FROM online_users 
            ORDER BY login_time DESC
        """)
        
        users = c.fetchall()
        
        if users:
            print(f"{'用户名':<20} {'IP地址':<15} {'登录时间':<20} {'页面'}")
            print("-" * 70)
            for user in users:
                username = user[0] or '未知'
                ip = user[1] or '未知'
                login_time = user[2][:19] if user[2] else '未知'
                page = user[3] or '/'
                print(f"{username:<20} {ip:<15} {login_time:<20} {page}")
        else:
            print("  没有在线用户")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 查询失败: {e}")

if __name__ == "__main__":
    print("🧹 测试数据清理工具")
    print("=" * 50)
    
    # 显示当前用户
    show_current_users()
    
    # 询问是否清理
    response = input("\n⚠️  是否清理所有测试用户数据? 这将删除所有在线用户和访问记录! (y/N): ")
    if response.lower() in ['y', 'yes']:
        confirm = input("\n🚨 确认删除所有数据? 此操作不可逆! (输入 'DELETE' 确认): ")
        if confirm == 'DELETE':
            clean_test_data()
            
            # 显示清理后的用户
            show_current_users()
        else:
            print("❌ 确认失败，取消清理操作")
    else:
        print("取消清理操作")