@echo off
echo 🔥 检查防火墙设置 - 8501端口
echo ================================

echo.
echo 📋 当前防火墙规则（8501端口）：
netsh advfirewall firewall show rule name="Streamlit 8501" verbose | findstr /C:"Enabled" /C:"Direction" /C:"Action" /C:"LocalPort"

echo.
echo 🔍 检查端口是否被防火墙阻止：
netsh advfirewall firewall show rule name=all | findstr /C:"8501"

echo.
echo 💡 如果没有看到8501端口的规则，需要添加防火墙例外
echo 💡 运行 add_firewall_rule.bat 来添加规则
pause