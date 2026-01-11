@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ========================================================================
echo     🔧 CÔNG CỤ QUẢN LÝ IP TĨNH MÁY IN
echo ========================================================================
echo.
echo Chọn công cụ:
echo.
echo   [1] 🖥️  Mở chương trình quản lý IP tĩnh (GUI)
echo   [0] ❌ Thoát
echo.
echo ========================================================================
echo.

set /p choice="Nhập lựa chọn (0-1): "

if "%choice%"=="1" goto gui
if "%choice%"=="0" goto end
goto menu

:gui
echo.
echo ========================================================================
echo 🖥️  MỞ CHƯƠNG TRÌNH QUẢN LÝ IP TĨNH...
echo ========================================================================
echo.
python IP\static_ip_manager.py
goto end

:end
echo.
echo Tạm biệt! 👋
timeout /t 2 >nul
exit
