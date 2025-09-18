#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
获取服务器信息脚本
显示正确的访问地址
"""

import socket
import subprocess
import sys
import platform

def get_local_ip():
    """获取本机IP地址"""
    try:
        # 方法1: 连接外部地址获取本机IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        try:
            # 方法2: 获取主机名对应IP
            hostname = socket.gethostname()
            ip = socket.gethostbyname(hostname)
            return ip if ip != "127.0.0.1" else None
        except:
            return None

def check_port_listening(port):
    """检查端口是否有服务在监听"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = s.connect_ex(('127.0.0.1', port))
        s.close()
        return result == 0
    except:
        return False

def get_all_ips():
    """获取所有网络接口IP地址"""
    ips = []
    try:
        if platform.system() == "Windows":
            result = subprocess.run(['ipconfig'], capture_output=True, text=True, encoding='gbk')
            lines = result.stdout.split('\n')
            for line in lines:
                if 'IPv4' in line and '地址' in line:
                    ip = line.split(':')[-1].strip()
                    if ip and ip != '127.0.0.1':
                        ips.append(ip)
        else:
            result = subprocess.run(['hostname', '-I'], capture_output=True, text=True)
            ips = result.stdout.strip().split()
    except:
        pass
    
    return [ip for ip in ips if not ip.startswith('169.254')]  # 过滤掉自动分配的IP

def main():
    print("🚗 无人驾驶数据管理平台 - 服务器访问地址")
    print("=" * 50)
    
    # 检查端口状态
    port_8501 = check_port_listening(8501)
    port_8502 = check_port_listening(8502)
    
    print(f"\n🔍 端口状态检查：")
    print(f"   8501端口：{'✅ 运行中' if port_8501 else '❌ 未使用'}")
    print(f"   8502端口：{'✅ 运行中' if port_8502 else '❌ 未使用'}")
    
    # 确定使用的端口
    active_port = None
    if port_8501:
        active_port = 8501
    elif port_8502:
        active_port = 8502
    
    # 获取本机IP
    local_ip = get_local_ip()
    all_ips = get_all_ips()
    
    print("\n📍 可用的访问地址：")
    
    if active_port:
        print(f"\n✅ 服务器正在运行（端口 {active_port}）：")
        print(f"   http://127.0.0.1:{active_port}")
        print(f"   http://localhost:{active_port}")
        
        if local_ip:
            print(f"   http://{local_ip}:{active_port}")
    else:
        print("\n⚠️ 服务器未检测到运行，预期地址：")
        print("   http://127.0.0.1:8501")
        print("   http://localhost:8501")
        
        if local_ip:
            print(f"   http://{local_ip}:8501")
    
    if all_ips and active_port:
        print(f"\n🌐 所有网络地址（端口 {active_port}）：")
        for ip in set(all_ips):
            print(f"   http://{ip}:{active_port}")
    
    print("\n" + "=" * 50)
    print("💡 使用说明：")
    if not active_port:
        print("• ❌ 服务器未运行，请先启动服务器")
        print("• 🚀 运行: start_central_server.bat 或 start_server_8501.bat")
    else:
        if active_port == 8502:
            print("• ⚠️ 服务器运行在8502端口（8501端口被占用）")
            print("• 💡 建议使用 start_server_8501.bat 强制使用8501端口")
        else:
            print("• ✅ 服务器正常运行在8501端口")
        print("• 🏠 本地访问：使用127.0.0.1地址")
        print("• 🌍 网络访问：使用实际IP地址")
    print("• 🔥 确保防火墙允许相应端口通信")

if __name__ == "__main__":
    main()