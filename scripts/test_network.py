#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
网络连通性测试脚本
"""

import socket
import subprocess
import platform

def test_port_connectivity():
    """测试端口连通性"""
    print("🌐 网络连通性测试")
    print("=" * 40)
    
    # 获取本机IP
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
    except:
        local_ip = "127.0.0.1"
    
    print(f"📍 服务器IP: {local_ip}")
    print(f"📍 测试端口: 8501")
    
    # 测试本地连接
    print(f"\n🏠 本地连接测试...")
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(3)
        result = s.connect_ex(('127.0.0.1', 8501))
        s.close()
        if result == 0:
            print("✅ 本地连接正常")
        else:
            print("❌ 本地连接失败")
    except Exception as e:
        print(f"❌ 本地连接异常: {e}")
    
    # 测试网络连接
    print(f"\n🌍 网络连接测试...")
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(3)
        result = s.connect_ex((local_ip, 8501))
        s.close()
        if result == 0:
            print("✅ 网络连接正常")
        else:
            print("❌ 网络连接失败")
    except Exception as e:
        print(f"❌ 网络连接异常: {e}")
    
    # 检查防火墙
    print(f"\n🔥 防火墙检查...")
    if platform.system() == "Windows":
        try:
            result = subprocess.run([
                'netsh', 'advfirewall', 'firewall', 'show', 'rule', 
                'name=all'
            ], capture_output=True, text=True)
            
            if '8501' in result.stdout:
                print("✅ 检测到8501端口防火墙规则")
            else:
                print("⚠️ 未检测到8501端口防火墙规则")
                print("💡 建议运行: scripts\\add_firewall_rule.bat")
        except:
            print("❓ 无法检查防火墙状态")
    
    print(f"\n📋 给其他电脑的访问地址:")
    print(f"   http://{local_ip}:8501")
    
    print(f"\n💡 故障排除建议:")
    print("1. 确保防火墙允许8501端口")
    print("2. 确保服务器和客户端在同一网络")
    print("3. 尝试ping服务器IP地址")
    print("4. 检查路由器是否阻止了连接")

if __name__ == "__main__":
    test_port_connectivity()