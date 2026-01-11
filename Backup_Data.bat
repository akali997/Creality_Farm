@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ========================================================================
echo     💾 BACKUP DỮ LIỆU CREALITY FARM
echo ========================================================================
echo.

REM Kiểm tra thư mục dữ liệu có tồn tại không
if not exist "C:\Creality\Data" (
    echo ❌ Không tìm thấy thư mục dữ liệu: C:\Creality\Data
    echo ⚠️ Có thể bạn chưa chạy phần mềm lần nào?
    echo.
    pause
    exit /b 1
)

REM Tạo tên file backup với timestamp
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set datetime=%%I
set TIMESTAMP=%datetime:~0,8%_%datetime:~8,6%
set BACKUP_NAME=CrealityFarm_Backup_%TIMESTAMP%

echo 📂 Thư mục nguồn: C:\Creality\Data
echo.

REM Hỏi người dùng chọn nơi lưu
echo Chọn nơi lưu backup:
echo.
echo   [1] Desktop (Khuyến nghị)
echo   [2] Documents
echo   [3] Tùy chọn (chọn thư mục)
echo   [0] Hủy
echo.

set /p choice="Nhập lựa chọn (0-3): "

if "%choice%"=="1" (
    set "BACKUP_DIR=%USERPROFILE%\Desktop\%BACKUP_NAME%"
) else if "%choice%"=="2" (
    set "BACKUP_DIR=%USERPROFILE%\Documents\%BACKUP_NAME%"
) else if "%choice%"=="3" (
    echo.
    echo 📁 Chọn thư mục đích...
    echo    (Sẽ tạo thư mục con "%BACKUP_NAME%" trong thư mục bạn chọn)
    echo.
    
    REM Mở dialog chọn thư mục (dùng PowerShell)
    for /f "delims=" %%I in ('powershell -command "Add-Type -AssemblyName System.Windows.Forms; $f = New-Object System.Windows.Forms.FolderBrowserDialog; $f.Description = 'Chọn thư mục lưu backup'; if($f.ShowDialog() -eq 'OK'){$f.SelectedPath}"') do set "SELECTED_PATH=%%I"
    
    if "!SELECTED_PATH!"=="" (
        echo ❌ Không chọn thư mục. Hủy backup.
        pause
        exit /b 1
    )
    
    set "BACKUP_DIR=!SELECTED_PATH!\%BACKUP_NAME%"
) else (
    echo ❌ Hủy backup.
    pause
    exit /b 0
)

echo.
echo ========================================================================
echo 💾 ĐANG BACKUP...
echo ========================================================================
echo.
echo Từ: C:\Creality\Data
echo Đến: %BACKUP_DIR%
echo.

REM Tạo thư mục backup
mkdir "%BACKUP_DIR%" 2>nul

REM Copy dữ liệu
xcopy "C:\Creality\Data\*.*" "%BACKUP_DIR%\" /E /I /Y /Q

if errorlevel 1 (
    echo.
    echo ❌ Backup thất bại!
    pause
    exit /b 1
)

echo.
echo ========================================================================
echo ✅ BACKUP THÀNH CÔNG!
echo ========================================================================
echo.
echo 📂 Vị trí: %BACKUP_DIR%
echo.
echo 📋 Các file đã backup:
dir /b "%BACKUP_DIR%"
echo.
echo 💡 Lưu ý:
echo    • Lưu folder này vào USB/Cloud để an toàn
echo    • Dùng script "Restore_Data.bat" để khôi phục
echo.

REM Hỏi có muốn mở thư mục không
set /p open="Mở thư mục backup? (Y/N): "
if /i "%open%"=="Y" (
    start explorer "%BACKUP_DIR%"
)

pause

