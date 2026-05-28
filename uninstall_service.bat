@echo off
:: AutoCamera 服务卸载脚本
:: 需要以管理员身份运行

net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [错误] 请右键此文件，选择"以管理员身份运行"
    pause
    exit /b 1
)

echo 正在停止 AutoCamera 进程...
taskkill /f /im AutoCamera.exe >nul 2>&1

echo 正在删除计划任务...
schtasks /delete /tn "AutoCamera" /f

if %errorLevel% equ 0 (
    echo [成功] 已卸载 AutoCamera 后台服务
) else (
    echo [提示] 计划任务不存在或已删除
)

pause
