@echo off
REM 点云可视化平台启动脚本 (Windows)

echo 🚀 启动无人驾驶数据管理平台
echo ==============================

REM 检查Python版本
echo 📋 检查Python环境...
python --version

REM 安装依赖包
echo 📦 安装依赖包...
pip install -r requirements.txt

REM 创建测试数据
echo 🧪 创建测试数据...
python test_pointcloud.py

REM 启动Streamlit应用
echo 🌐 启动Web应用...
echo 💡 应用将在浏览器中自动打开
echo 📍 如果没有自动打开，请访问: http://localhost:8501
echo.

streamlit run main.py

pause