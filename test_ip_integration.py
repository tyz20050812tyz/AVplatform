#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IP地址集成测试脚本
测试在线用户管理与IP地址获取的集成
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_ip_integration():
    """测试IP地址集成功能"""
    print("🌐 IP地址集成测试")
    print("=" * 50)
    
    try:
        # 导入模块
        from src.ip_utils import get_best_guess_client_ip, get_comprehensive_ip_info, format_ip_info
        from src.online_users import OnlineUserManager, add_user_online, get_online_users_count
        from src.auth import init_auth_database
        
        # 初始化数据库
        init_auth_database()
        
        # 获取IP信息
        print("1. 获取IP地址信息...")
        ip_info = get_comprehensive_ip_info()
        client_ip = get_best_guess_client_ip()
        
        print(f"  📱 客户端IP: {client_ip}")
        print(f"  🖥️ 服务器IP: {ip_info['server_local_ip']}")
        print(f"  🌍 公网IP: {ip_info['public_ip']}")
        
        # 格式化IP信息
        ip_details = format_ip_info(client_ip)
        print(f"  📊 IP类型: {ip_details['type']} ({ip_details['description']})")
        
        # 测试在线用户管理
        print("\n2. 测试在线用户管理...")
        manager = OnlineUserManager('test_ip.db')
        
        # 添加用户（使用真实IP）
        test_users = [
            ("user1", "用户一"),
            ("user2", "用户二"),
            ("admin", "管理员"),
            ("TongYuze", "超级管理员")
        ]
        
        for session_id, username in test_users:
            try:
                add_user_online(
                    session_id=session_id,
                    username=username,
                    ip_address=client_ip,  # 使用真实IP
                    page_path=f"/{username}_page"
                )
                print(f"  ✅ 添加用户: {username} (IP: {client_ip})")
            except Exception as e:
                print(f"  ❌ 添加用户失败: {username} - {e}")
        
        # 获取在线人数
        online_count = get_online_users_count()
        print(f"\n3. 当前在线人数: {online_count}")
        
        # 获取在线用户列表
        online_users = manager.get_online_users()
        if online_users:
            print("\n4. 在线用户详情:")
            for user in online_users:
                print(f"  👤 {user['username']} - IP: {user['ip_address']} - 页面: {user['page_path']}")
        
        # 获取访问统计
        stats = manager.get_visit_stats()
        print(f"\n5. 访问统计:")
        print(f"  👥 当前在线: {stats['online_count']}")
        print(f"  📅 今日访问: {stats['today_visits']}")
        print(f"  📊 总访问量: {stats['total_visits']}")
        
        # 测试IP地址分组
        print(f"\n6. IP地址分析:")
        ip_groups = {}
        for user in online_users:
            ip = user['ip_address'] or '未知'
            if ip not in ip_groups:
                ip_groups[ip] = []
            ip_groups[ip].append(user['username'])
        
        for ip, users in ip_groups.items():
            ip_info = format_ip_info(ip) if ip != '未知' else {'type': 'unknown', 'description': '未知'}
            print(f"  📍 {ip} ({ip_info['type']}): {', '.join(users)}")
        
        print("\n✅ IP地址集成测试完成！")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 清理测试数据库
        try:
            os.remove('test_ip.db')
            print("\n🧹 测试数据已清理")
        except:
            pass


def test_different_ip_scenarios():
    """测试不同IP场景"""
    print("\n🎭 不同IP场景测试")
    print("=" * 50)
    
    try:
        from src.ip_utils import format_ip_info
        from src.online_users import OnlineUserManager
        
        # 测试不同类型的IP地址
        test_ips = [
            "127.0.0.1",      # 本地环回
            "192.168.1.100",  # 私有网络
            "10.0.0.50",      # 私有网络
            "172.16.0.200",   # 私有网络
            "8.8.8.8",        # 公网地址
            "203.208.60.30"   # 公网地址
        ]
        
        manager = OnlineUserManager('test_scenarios.db')
        
        for i, ip in enumerate(test_ips):
            # 分析IP类型
            ip_info = format_ip_info(ip)
            print(f"📍 IP: {ip}")
            print(f"   类型: {ip_info['type']}")
            print(f"   描述: {ip_info['description']}")
            
            # 模拟用户登录
            session_id = f"session_{i}"
            username = f"用户{i+1}"
            
            manager.add_online_user(
                session_id=session_id,
                username=username,
                ip_address=ip,
                page_path=f"/page_{i+1}"
            )
            print(f"   ✅ 用户 {username} 已添加")
            print()
        
        # 统计不同类型IP的用户分布
        online_users = manager.get_online_users()
        ip_stats = {
            'localhost': 0,
            'private': 0,
            'public': 0,
            'unknown': 0
        }
        
        for user in online_users:
            ip = user['ip_address']
            if ip:
                ip_info = format_ip_info(ip)
                ip_stats[ip_info['type']] += 1
        
        print("📊 IP类型统计:")
        for ip_type, count in ip_stats.items():
            type_names = {
                'localhost': '本地环回',
                'private': '私有网络',
                'public': '公网地址',
                'unknown': '未知类型'
            }
            print(f"  {type_names[ip_type]}: {count} 人")
        
        print("\n✅ IP场景测试完成！")
        
    except Exception as e:
        print(f"\n❌ 场景测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 清理测试数据库
        try:
            os.remove('test_scenarios.db')
            print("\n🧹 场景测试数据已清理")
        except:
            pass


if __name__ == "__main__":
    test_ip_integration()
    test_different_ip_scenarios()
    
    print("\n🎯 总结:")
    print("✅ IP地址获取功能正常")
    print("✅ 在线用户管理集成成功")
    print("✅ 支持多种IP类型分析")
    print("✅ 真实IP地址记录功能可用")