@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ========================================================================
echo     🔄 RESTORE DỮ LIỆU CREALITY FARM
echo ========================================================================
echo.

echo ⚠️ CẢNH BÁO:
echo    Restore sẽ GHI ĐÈ dữ liệu hiện tại!
echo    Nếu chưa backup, hãy chạy "Backup_Data.bat" trước.
echo.

set /p confirm="Bạn có chắc muốn tiếp tục? (Y/N): "
if /i not "%confirm%"=="Y" (
    echo ❌ Đã hủy restore.
    pause
    exit /b 0
)

echo.
echo 📁 Chọn thư mục backup để restore...
echo.

REM Mở dialog chọn thư mục backup
for /f "delims=" %%I in ('powershell -command "Add-Type -AssemblyName System.Windows.Forms; $f = New-Object System.Windows.Forms.FolderBrowserDialog; $f.Description = 'Chọn thư mục backup (VD: CrealityFarm_Backup_...)'; if($f.ShowDialog() -eq 'OK'){$f.SelectedPath}"') do set "BACKUP_DIR=%%I"

if "%BACKUP_DIR%"=="" (
    echo ❌ Không chọn thư mục. Hủy restore.
    pause
    exit /b 1
)

echo.
echo 📂 Thư mục backup: %BACKUP_DIR%
echo.

REM Kiểm tra thư mục backup có file không
if not exist "%BACKUP_DIR%\*.json" (
    echo ❌ Thư mục không chứa file backup hợp lệ!
    echo ⚠️ Vui lòng chọn đúng thư mục backup (có chứa file .json)
    pause
    exit /b 1
)

echo 📋 Các file sẽ restore:
dir /b "%BACKUP_DIR%"
echo.

set /p final_confirm="Xác nhận restore? (Y/N): "
if /i not "%final_confirm%"=="Y" (
    echo ❌ Đã hủy restore.
    pause
    exit /b 0
)

echo.
echo ========================================================================
echo 🔄 ĐANG RESTORE...
echo ========================================================================
echo.

REM Tạo thư mục đích nếu chưa có
if not exist "C:\Creality\Data" (
    mkdir "C:\Creality\Data"
)

REM Copy dữ liệu
xcopy "%BACKUP_DIR%\*.*" "C:\Creality\Data\" /E /I /Y /Q

if errorlevel 1 (
    echo.
    echo ❌ Restore thất bại!
    pause
    exit /b 1
)

echo.
echo ========================================================================
echo ✅ RESTORE THÀNH CÔNG!
echo ========================================================================
echo.
echo 📂 Dữ liệu đã được khôi phục vào: C:\Creality\Data
echo.
echo 💡 Bước tiếp theo:
echo    • Mở lại phần mềm Creality Farm
echo    • Kiểm tra thống kê và cài đặt
echo.

pause

