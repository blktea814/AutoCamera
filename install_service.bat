@echo off
:: AutoCamera 锁屏自启服务安装脚本
:: 需要以管理员身份运行

echo ============================================
echo   AutoCamera 后台服务安装
echo   安装后程序将在开机时自动启动
echo   即使锁屏也会持续运行
echo ============================================
echo.

net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [错误] 请右键此文件，选择"以管理员身份运行"
    pause
    exit /b 1
)

set EXE_PATH=%~dp0dist\AutoCamera.exe
if not exist "%EXE_PATH%" (
    echo [错误] 未找到 AutoCamera.exe
    echo 请先运行 python build.py 进行打包
    pause
    exit /b 1
)

echo 正在创建计划任务...

schtasks /create /tn "AutoCamera" /tr "\"%EXE_PATH%\" --background" /sc onlogon /rl highest /f

if %errorLevel% equ 0 (
    echo.
    echo [成功] 计划任务已创建！
    echo   - 任务名称: AutoCamera
    echo   - 触发条件: 用户登录时自动启动
    echo   - 权限级别: 最高权限
    echo   - 锁屏运行: 是（进程不会因锁屏终止）
    echo.
    echo 如需卸载，请运行 uninstall_service.bat
) else (
    echo [错误] 创建计划任务失败
)

pause
