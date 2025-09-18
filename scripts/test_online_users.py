#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
在线用户功能测试脚本
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.online_users import OnlineUserManager
import time
import random

def test_online_users():
    """测试在线用户功能"""
    print("🧪 测试在线用户功能")
    print("=" * 40)
    
    # 创建管理器
    manager = OnlineUserManager('test_online.db')
    
    # 模拟添加用户
    print("1. 添加测试用户...")
    test_users = [
        ("session_001", "用户A", "192.168.1.100", "/首页"),
        ("session_002", "用户B", "192.168.1.101", "/数据上传"),
        ("session_003", "游客", "192.168.1.102", "/数据浏览"),
        ("session_004", "TongYuze", "192.168.1.103", "/管理员设置"),
    ]
    
    for session_id, username, ip, page in test_users:
        manager.add_online_user(session_id, username, ip, page_path=page)
        print(f"  ✅ 添加用户: {username} ({ip})")
    
    # 测试获取在线人数
    print(f"\n2. 当前在线人数: {manager.get_online_count()}")
    
    # 测试获取在线用户列表
    print("\n3. 在线用户列表:")
    users = manager.get_online_users()
    for user in users:
        print(f"  👤 {user['username']} - {user['page_path']} - {user['online_duration']}")
    
    # 测试更新用户活动
    print("\n4. 更新用户活动...")
    manager.update_user_activity("session_001", "/数据可视化")
    print("  ✅ 用户A 切换到数据可视化页面")
    
    # 测试获取访问统计
    print("\n5. 访问统计:")
    stats = manager.get_visit_stats()
    print(f"  👥 当前在线: {stats['online_count']}")
    print(f"  📅 今日访问: {stats['today_visits']}")
    print(f"  📊 总访问量: {stats['total_visits']}")
    
    # 测试用户下线
    print("\n6. 用户下线...")
    manager.remove_user("session_002")
    print("  ✅ 用户B 已下线")
    print(f"  当前在线人数: {manager.get_online_count()}")
    
    # 测试清理无效用户
    print("\n7. 测试清理无效用户...")
    print("  等待5秒后清理...")
    time.sleep(2)  # 缩短等待时间
    manager.cleanup_inactive_users()
    print(f"  清理后在线人数: {manager.get_online_count()}")
    
    print("\n✅ 测试完成！")
    
    # 清理测试文件
    try:
        os.remove('test_online.db')
        print("🧹 测试文件已清理")
    except:
        pass

def test_integration():
    """测试集成功能"""
    print("\n🔗 测试集成功能")
    print("=" * 40)
    
    try:
        from src.online_users import get_online_users_count, add_user_online, track_user_online
        
        # 测试便捷函数
        print("1. 测试便捷函数...")
        
        # 添加用户
        add_user_online("test_session", "测试用户", "127.0.0.1", "/测试页面")
        print("  ✅ 添加用户成功")
        
        # 获取在线人数
        count = get_online_users_count()
        print(f"  当前在线人数: {count}")
        
        # 跟踪用户活动
        track_user_online("test_session", "/新页面")
        print("  ✅ 跟踪活动成功")
        
        print("✅ 集成测试通过")
        
    except Exception as e:
        print(f"❌ 集成测试失败: {e}")

if __name__ == "__main__":
    test_online_users()
    test_integration()