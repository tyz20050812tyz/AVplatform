@echo off
echo 🔥 添加防火墙规则 - 允许8501端口
echo ================================

echo 正在添加入站规则...
netsh advfirewall firewall add rule name="Streamlit 8501 Inbound" dir=in action=allow protocol=TCP localport=8501

echo 正在添加出站规则...
netsh advfirewall firewall add rule name="Streamlit 8501 Outbound" dir=out action=allow protocol=TCP localport=8501

echo.
echo ✅ 防火墙规则添加完成！
echo 💡 现在其他电脑应该可以访问：http://192.168.189.147:8501
echo.

pause