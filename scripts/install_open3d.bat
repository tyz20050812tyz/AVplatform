@echo off
REM Open3D 依赖安装脚本
REM 解决 Python 3.13 兼容性问题

echo ========================================
echo Open3D 依赖安装脚本
echo ========================================
echo.

REM 检测 Python 版本
echo 检测 Python 版本...
python --version
py --version
echo.

REM 显示问题说明
echo 问题说明：
echo - Python 3.13 是最新版本，但 Open3D 库暂时不支持
echo - Open3D 目前支持 Python 3.8-3.11
echo.

echo 解决方案选择：
echo 1. 继续使用当前环境（跳过 Open3D，功能降级）
echo 2. 安装 Python 3.11 并创建虚拟环境（推荐）
echo 3. 使用 Conda 环境管理
echo.

set /p choice="请选择解决方案 (1/2/3): "

if "%choice%"=="1" goto skip_open3d
if "%choice%"=="2" goto install_python311
if "%choice%"=="3" goto use_conda
goto invalid_choice

:skip_open3d
echo.
echo 选择方案 1: 跳过 Open3D 安装
echo 正在安装其他依赖...
py -m pip install -r config/requirements.txt --skip-errors
echo.
echo 注意：点云可视化功能将受限，但其他功能正常
echo 程序会自动检测并提供备用方案
goto end

:install_python311
echo.
echo 选择方案 2: 安装 Python 3.11
echo 请访问以下链接下载 Python 3.11：
echo https://www.python.org/downloads/release/python-3118/
echo.
echo 安装完成后，使用以下命令创建虚拟环境：
echo python3.11 -m venv venv
echo venv\Scripts\activate
echo pip install -r config/requirements.txt
goto end

:use_conda
echo.
echo 选择方案 3: 使用 Conda
echo 如果您有 Conda，请运行：
echo conda create -n pointcloud python=3.11
echo conda activate pointcloud
echo conda install -c conda-forge open3d
echo pip install -r config/requirements.txt
goto end

:invalid_choice
echo 无效选择，请重新运行脚本
goto end

:end
echo.
echo 安装脚本执行完成
pause