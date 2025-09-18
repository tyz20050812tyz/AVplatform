#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
服务器部署脚本
将平台部署为中央服务器，统一管理所有用户数据
"""

import streamlit as st
import socket
import subprocess
import sys
import os
from pathlib import Path

def get_local_ip():
    """获取本机IP地址"""
    try:
        # 连接到外部地址来获取本机IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def check_port_available(port):
    """检查端口是否可用"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(("", port))
        s.close()
        return True
    except:
        return False

def deploy_server():
    """部署服务器"""
    st.title("🚀 平台服务器部署")
    
    st.markdown("""
    ## 📋 部署说明
    
    部署后，您的电脑将作为中央服务器运行，其他用户可以通过网络访问平台：
    - 所有用户数据将统一存储在您的电脑上
    - 您可以管理所有用户上传的数据
    - 功能建议和问题反馈都会集中到您这里
    """)
    
    # 获取本机IP
    local_ip = get_local_ip()
    st.info(f"🖥️ 检测到您的IP地址: {local_ip}")
    
    # 端口配置
    st.subheader("⚙️ 服务器配置")
    
    col1, col2 = st.columns(2)
    with col1:
        port = st.number_input("服务器端口", min_value=1000, max_value=65535, value=8501)
        
    with col2:
        allow_external = st.checkbox("允许外部访问", value=True, help="勾选后其他电脑可以访问")
    
    # 检查端口是否可用
    if check_port_available(port):
        st.success(f"✅ 端口 {port} 可用")
    else:
        st.error(f"❌ 端口 {port} 已被占用，请选择其他端口")
        return
    
    # 访问地址预览
    st.subheader("🌐 访问地址")
    
    if allow_external:
        st.code(f"http://{local_ip}:{port}")
        st.info("其他用户可以使用上述地址访问平台")
    else:
        st.code(f"http://127.0.0.1:{port}")
        st.info("仅本机可以访问")
    
    # 数据存储位置
    st.subheader("💾 数据存储")
    
    project_root = Path(__file__).parent.parent
    data_path = project_root / "data"
    datasets_path = project_root / "datasets"
    
    st.write(f"**数据库文件**: `{project_root}/data.db`")
    st.write(f"**用户数据**: `{data_path}`")
    st.write(f"**上传文件**: `{datasets_path}`")
    
    # 部署按钮
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🚀 启动服务器", type="primary"):
            start_server(port, allow_external)
    
    with col2:
        if st.button("📋 生成启动脚本"):
            generate_startup_script(port, allow_external)

def start_server(port, allow_external=True):
    """启动服务器"""
    try:
        # 构建启动命令
        project_root = Path(__file__).parent.parent
        main_file = project_root / "src" / "main.py"
        
        cmd = [
            sys.executable, "-m", "streamlit", "run", 
            str(main_file),
            "--server.port", str(port),
        ]
        
        if allow_external:
            cmd.extend(["--server.address", "0.0.0.0"])
        
        st.success("🚀 正在启动服务器...")
        st.info("服务器将在新窗口中运行，请不要关闭命令行窗口")
        
        # 启动服务器
        subprocess.Popen(cmd, creationflags=subprocess.CREATE_NEW_CONSOLE)
        
        st.balloons()
        
    except Exception as e:
        st.error(f"启动失败: {e}")

def generate_startup_script(port, allow_external=True):
    """生成启动脚本"""
    try:
        project_root = Path(__file__).parent.parent
        
        # Windows批处理脚本
        bat_content = f"""@echo off
echo 🚀 启动无人驾驶数据管理平台服务器
echo.
echo 📍 服务器地址: http://{"0.0.0.0" if allow_external else "127.0.0.1"}:{port}
echo 💾 数据存储: {project_root}
echo.

cd /d "{project_root}"
python -m streamlit run src/main.py --server.port {port}{"" if not allow_external else " --server.address 0.0.0.0"}

pause
"""
        
        bat_file = project_root / "start_server.bat"
        with open(bat_file, 'w', encoding='utf-8') as f:
            f.write(bat_content)
        
        # Linux/Mac shell脚本
        sh_content = f"""#!/bin/bash
echo "🚀 启动无人驾驶数据管理平台服务器"
echo ""
echo "📍 服务器地址: http://{"0.0.0.0" if allow_external else "127.0.0.1"}:{port}"
echo "💾 数据存储: {project_root}"
echo ""

cd "{project_root}"
python -m streamlit run src/main.py --server.port {port}{"" if not allow_external else " --server.address 0.0.0.0"}
"""
        
        sh_file = project_root / "start_server.sh"
        with open(sh_file, 'w', encoding='utf-8') as f:
            f.write(sh_content)
        
        # 设置执行权限
        try:
            os.chmod(sh_file, 0o755)
        except:
            pass
        
        st.success("✅ 启动脚本生成成功！")
        st.write(f"**Windows**: `{bat_file}`")
        st.write(f"**Linux/Mac**: `{sh_file}`")
        st.info("双击批处理文件即可启动服务器")
        
    except Exception as e:
        st.error(f"生成脚本失败: {e}")

if __name__ == "__main__":
    deploy_server()