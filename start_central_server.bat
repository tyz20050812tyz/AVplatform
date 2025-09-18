@echo off
REM 无人驾驶数据管理平台 - 中央服务器启动脚本

echo =====================================
echo  🚗 无人驾驶数据管理平台 - 中央服务器
echo =====================================
echo.

REM 获取本机IP地址
echo 🔍 正在检测网络地址...
python scripts/get_server_info.py
echo.

echo 🚀 正在启动服务器...
echo 📝 请保持此窗口开启，关闭将停止服务器
echo 💡 服务器启动后，请使用上面显示的地址访问
echo.

REM 切换到项目目录
cd /d "%~dp0"

REM 启动Streamlit服务器
python -m streamlit run src/main.py --server.port 8501 --server.address 127.0.0.1

echo.
echo ⚠️  服务器已停止
pause