#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IP地址获取工具模块
支持多种方式获取客户端IP地址
"""

import os
import socket
import subprocess
import requests
from typing import Optional


def get_client_ip_from_streamlit() -> Optional[str]:
    """
    尝试从Streamlit上下文获取客户端IP地址
    注意：Streamlit默认不提供直接获取客户端IP的方法
    """
    try:
        # 尝试从环境变量获取（某些部署环境可能会设置）
        client_ip = os.environ.get('HTTP_X_FORWARDED_FOR')
        if client_ip:
            # 如果有多个IP，取第一个
            return client_ip.split(',')[0].strip()
        
        client_ip = os.environ.get('HTTP_X_REAL_IP')
        if client_ip:
            return client_ip.strip()
        
        client_ip = os.environ.get('REMOTE_ADDR')
        if client_ip:
            return client_ip.strip()
            
    except Exception:
        pass
    
    return None


def get_server_local_ip() -> Optional[str]:
    """获取服务器本地IP地址"""
    try:
        # 连接到外部地址来获取本地IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        try:
            # 备选方法：获取hostname对应的IP
            hostname = socket.gethostname()
            return socket.gethostbyname(hostname)
        except Exception:
            return None


def get_public_ip() -> Optional[str]:
    """获取公网IP地址（需要网络连接）"""
    services = [
        'https://api.ipify.org',
        'https://icanhazip.com',
        'https://ident.me',
        'https://httpbin.org/ip'
    ]
    
    for service in services:
        try:
            response = requests.get(service, timeout=5)
            if response.status_code == 200:
                ip = response.text.strip()
                # 处理httpbin.org的JSON响应
                if service.endswith('/ip'):
                    import json
                    ip = json.loads(ip)['origin']
                return ip
        except Exception:
            continue
    
    return None


def get_network_interfaces() -> dict:
    """获取所有网络接口的IP地址"""
    interfaces = {}
    
    try:
        # Windows
        if os.name == 'nt':
            result = subprocess.run(['ipconfig'], capture_output=True, text=True, encoding='gbk')
            lines = result.stdout.split('\n')
            current_adapter = None
            
            for line in lines:
                line = line.strip()
                if '适配器' in line or 'adapter' in line.lower():
                    current_adapter = line
                elif 'IPv4' in line and ':' in line:
                    ip = line.split(':')[-1].strip()
                    if current_adapter and ip:
                        interfaces[current_adapter] = ip
        
        # Linux/Mac
        else:
            result = subprocess.run(['ifconfig'], capture_output=True, text=True)
            lines = result.stdout.split('\n')
            current_interface = None
            
            for line in lines:
                if line and not line.startswith(' '):
                    current_interface = line.split(':')[0]
                elif 'inet ' in line and current_interface:
                    parts = line.strip().split()
                    for i, part in enumerate(parts):
                        if part == 'inet' and i + 1 < len(parts):
                            ip = parts[i + 1]
                            if not ip.startswith('127.'):
                                interfaces[current_interface] = ip
                            break
    
    except Exception:
        pass
    
    return interfaces


def get_best_guess_client_ip() -> str:
    """
    获取最佳猜测的客户端IP地址
    按优先级尝试不同方法
    """
    # 1. 尝试从Streamlit上下文获取
    client_ip = get_client_ip_from_streamlit()
    if client_ip and not client_ip.startswith('127.'):
        return client_ip
    
    # 2. 如果是本地访问，返回本地IP
    local_ip = get_server_local_ip()
    if local_ip:
        return local_ip
    
    # 3. 备选：返回localhost
    return '127.0.0.1'


def format_ip_info(ip_address: str) -> dict:
    """格式化IP地址信息"""
    info = {
        'ip': ip_address,
        'type': 'unknown',
        'description': '未知'
    }
    
    if ip_address.startswith('127.'):
        info['type'] = 'localhost'
        info['description'] = '本地环回'
    elif ip_address.startswith('192.168.') or ip_address.startswith('10.') or ip_address.startswith('172.'):
        info['type'] = 'private'
        info['description'] = '私有网络'
    else:
        info['type'] = 'public'
        info['description'] = '公网地址'
    
    return info


def get_comprehensive_ip_info() -> dict:
    """获取综合的IP地址信息"""
    return {
        'client_ip': get_best_guess_client_ip(),
        'server_local_ip': get_server_local_ip(),
        'public_ip': get_public_ip(),
        'network_interfaces': get_network_interfaces(),
        'client_from_env': get_client_ip_from_streamlit()
    }


# 测试函数
if __name__ == "__main__":
    print("🌐 IP地址获取测试")
    print("=" * 50)
    
    info = get_comprehensive_ip_info()
    
    print(f"📱 客户端IP (最佳猜测): {info['client_ip']}")
    print(f"🖥️ 服务器本地IP: {info['server_local_ip']}")
    print(f"🌍 公网IP: {info['public_ip']}")
    print(f"🔍 环境变量客户端IP: {info['client_from_env']}")
    
    print(f"\n🔌 网络接口:")
    for interface, ip in info['network_interfaces'].items():
        print(f"  - {interface}: {ip}")
    
    # 格式化信息
    client_info = format_ip_info(info['client_ip'])
    print(f"\n📊 客户端IP信息:")
    print(f"  - IP: {client_info['ip']}")
    print(f"  - 类型: {client_info['type']}")
    print(f"  - 描述: {client_info['description']}")