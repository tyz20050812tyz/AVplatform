#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模拟不同IP用户脚本
创建具有不同IP地址的测试用户，便于演示IP地址功能
"""

import sqlite3
import sys
import os
from datetime import datetime

# 添加src路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

def simulate_users_with_different_ips():
    """模拟具有不同IP地址的用户"""
    print("🎭 模拟不同IP地址的用户...")
    
    # 模拟用户数据
    users = [
        ("北京用户", "59.66.139.11", "首页"),       # 北京公网IP
        ("上海用户", "180.153.78.25", "数据上传"),   # 上海公网IP
        ("广州用户", "113.108.168.55", "数据浏览"),  # 广州公网IP
        ("深圳用户", "119.123.45.67", "数据可视化"), # 深圳公网IP
        ("本地用户1", "192.168.1.100", "首页"),      # 局域网IP
        ("本地用户2", "192.168.1.101", "使用文档"),  # 局域网IP
        ("办公室用户", "10.0.0.50", "功能建议"),     # 办公网IP
        ("测试用户", "127.0.0.1", "问题反馈"),       # 本地IP
    ]
    
    try:
        conn = sqlite3.connect('data.db')
        c = conn.cursor()
        
        current_time = datetime.now().isoformat()
        
        for i, (username, ip, page) in enumerate(users):
            session_id = f"session_{username}_{i}"
            
            # 插入在线用户
            c.execute('''
                INSERT OR REPLACE INTO online_users 
                (session_id, username, ip_address, login_time, last_seen, page_path, is_active)
                VALUES (?, ?, ?, ?, ?, ?, 1)
            ''', (session_id, username, ip, current_time, current_time, f"/{page}"))
            
            # 插入访问日志
            c.execute('''
                INSERT INTO user_visits (session_id, username, ip_address, visit_time, page_path, action)
                VALUES (?, ?, ?, ?, ?, 'login')
            ''', (session_id, username, ip, current_time, f"/{page}"))
            
            print(f"  ✅ 创建用户: {username} (IP: {ip})")
        
        conn.commit()
        conn.close()
        
        print(f"\n✅ 成功创建 {len(users)} 个模拟用户")
        
    except Exception as e:
        print(f"❌ 创建失败: {e}")

def analyze_ip_distribution():
    """分析IP地址分布"""
    print("\n📊 IP地址分布分析:")
    
    try:
        conn = sqlite3.connect('data.db')
        c = conn.cursor()
        
        c.execute("SELECT ip_address, COUNT(*) as count FROM online_users GROUP BY ip_address ORDER BY count DESC")
        ip_stats = c.fetchall()
        
        # IP类型分类
        ip_types = {
            'localhost': 0,    # 127.x.x.x
            'private': 0,      # 192.168.x.x, 10.x.x.x, 172.16-31.x.x
            'public': 0,       # 其他
            'unknown': 0       # None或空
        }
        
        print(f"{'IP地址':<15} {'用户数':<8} {'类型'}")
        print("-" * 35)
        
        for ip, count in ip_stats:
            if not ip:
                ip_type = 'unknown'
                type_name = '未知'
            elif ip.startswith('127.'):
                ip_type = 'localhost' 
                type_name = '本地环回'
            elif (ip.startswith('192.168.') or ip.startswith('10.') or 
                  ip.startswith('172.16.') or ip.startswith('172.17.') or
                  ip.startswith('172.18.') or ip.startswith('172.19.') or
                  ip.startswith('172.20.') or ip.startswith('172.21.') or
                  ip.startswith('172.22.') or ip.startswith('172.23.') or
                  ip.startswith('172.24.') or ip.startswith('172.25.') or
                  ip.startswith('172.26.') or ip.startswith('172.27.') or
                  ip.startswith('172.28.') or ip.startswith('172.29.') or
                  ip.startswith('172.30.') or ip.startswith('172.31.')):
                ip_type = 'private'
                type_name = '私有网络'
            else:
                ip_type = 'public'
                type_name = '公网地址'
            
            ip_types[ip_type] += count
            ip_display = ip or '未知'
            print(f"{ip_display:<15} {count:<8} {type_name}")
        
        print(f"\n📈 类型统计:")
        for type_key, count in ip_types.items():
            if count > 0:
                type_names = {
                    'localhost': '本地环回',
                    'private': '私有网络', 
                    'public': '公网地址',
                    'unknown': '未知类型'
                }
                print(f"  {type_names[type_key]}: {count} 人")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 分析失败: {e}")

if __name__ == "__main__":
    print("🎭 IP地址用户模拟器")
    print("=" * 50)
    
    response = input("是否创建模拟用户数据? (y/N): ")
    if response.lower() in ['y', 'yes']:
        simulate_users_with_different_ips()
    
    # 分析IP分布
    analyze_ip_distribution()