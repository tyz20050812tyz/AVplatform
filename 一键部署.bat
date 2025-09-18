@echo off
echo =====================================
echo  🚗 无人驾驶数据管理平台 - 一键部署
echo =====================================
echo.

echo 📋 第一步：检查服务器状态
python scripts/get_server_info.py
echo.

echo 📋 第二步：显示部署信息
echo.
echo 🎯 部署完成！其他人可以通过以下方式访问：
echo.
echo 👥 用户访问地址：
echo    http://192.168.189.147:8502
echo.
echo 🔑 管理员登录：
echo    用户名：TongYuze
echo    密码：20050812
echo.
echo 📁 数据存储位置：
echo    %cd%\data.db （数据库）
echo    %cd%\datasets\ （用户文件）
echo    %cd%\data\ （反馈数据）
echo.

echo 📋 第三步：防火墙设置检查
echo.
echo ⚠️  如果其他人无法访问，请检查防火墙：
echo    1. 按 Win+I 打开设置
echo    2. 网络和Internet → Windows安全中心
echo    3. 防火墙和网络保护 → 允许应用通过防火墙
echo    4. 确保Python允许"专用"和"公用"网络
echo.

echo 📋 第四步：快速访问
echo.
set /p open_browser="是否打开访问页面？(y/n): "
if /i "%open_browser%"=="y" (
    start 访问平台.html
    echo ✅ 已打开访问页面
) else (
    echo 💡 您可以随时双击"访问平台.html"文件快速访问
)

echo.
echo 🎉 部署完成！
echo 📚 详细说明请查看：部署教程.md
echo.
pause