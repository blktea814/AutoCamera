import os
import plistlib
import subprocess
import sys
from typing import Tuple

from utils.paths import APP_NAME, PROJECT_ROOT, app_data_dir


MAC_LABEL = "com.blktea814.autocamera"


def _run(command) -> subprocess.CompletedProcess:
    return subprocess.run(command, capture_output=True, text=True)


def _windows_program_path() -> str:
    if getattr(sys, "frozen", False):
        return os.path.abspath(sys.executable)
    return os.path.join(PROJECT_ROOT, "dist", "AutoCamera.exe")


def _mac_program_arguments() -> list:
    if getattr(sys, "frozen", False):
        return [os.path.abspath(sys.executable), "--background"]
    return [sys.executable, os.path.join(PROJECT_ROOT, "main.py"), "--background"]


def _mac_plist_path() -> str:
    return os.path.join(os.path.expanduser("~"), "Library", "LaunchAgents", f"{MAC_LABEL}.plist")


def _mac_launchctl(*args) -> subprocess.CompletedProcess:
    return _run(["launchctl", *args])


def is_enabled() -> bool:
    if sys.platform == "win32":
        try:
            return _run(["schtasks", "/query", "/tn", APP_NAME]).returncode == 0
        except OSError:
            return False
    if sys.platform == "darwin":
        return os.path.exists(_mac_plist_path())
    return False


def enable() -> Tuple[bool, str]:
    if sys.platform == "win32":
        exe_path = _windows_program_path()
        if not os.path.exists(exe_path):
            return False, "未找到 AutoCamera.exe，请先运行 build.py 打包"
        try:
            result = _run([
                "schtasks", "/create", "/tn", APP_NAME,
                "/tr", f'"{exe_path}" --background',
                "/sc", "onlogon", "/rl", "highest", "/f",
            ])
        except OSError as exc:
            return False, str(exc)
        if result.returncode == 0:
            return True, "已启用开机自启和锁屏运行"
        return False, f"需要管理员权限，请以管理员身份运行程序\n{result.stderr.strip()}"

    if sys.platform == "darwin":
        plist_path = _mac_plist_path()
        os.makedirs(os.path.dirname(plist_path), exist_ok=True)
        state_dir = app_data_dir()
        os.makedirs(state_dir, exist_ok=True)
        payload = {
            "Label": MAC_LABEL,
            "ProgramArguments": _mac_program_arguments(),
            "RunAtLoad": True,
            # Do not relaunch the app after the user explicitly chooses
            # "退出" from the tray menu.
            "KeepAlive": False,
            "WorkingDirectory": PROJECT_ROOT,
            "StandardOutPath": os.path.join(state_dir, "autostart.stdout.log"),
            "StandardErrorPath": os.path.join(state_dir, "autostart.stderr.log"),
        }
        try:
            with open(plist_path, "wb") as f:
                plistlib.dump(payload, f, sort_keys=False)
            os.chmod(plist_path, 0o600)
            uid = str(os.getuid())
            _mac_launchctl("bootout", f"gui/{uid}", plist_path)
            result = _mac_launchctl("bootstrap", f"gui/{uid}", plist_path)
        except OSError as exc:
            return False, str(exc)
        if result.returncode == 0:
            return True, "已启用登录自启（锁屏后继续运行，摄像头权限取决于 macOS 设置）"
        try:
            os.remove(plist_path)
        except OSError:
            pass
        return False, f"无法加载 macOS LaunchAgent：{result.stderr.strip()}"

    return False, "当前系统暂不支持开机自启"


def disable() -> Tuple[bool, str]:
    if sys.platform == "win32":
        try:
            result = _run(["schtasks", "/delete", "/tn", APP_NAME, "/f"])
        except OSError as exc:
            return False, str(exc)
        return (True, "已关闭开机自启") if result.returncode == 0 else (False, result.stderr.strip())

    if sys.platform == "darwin":
        plist_path = _mac_plist_path()
        try:
            uid = str(os.getuid())
            _mac_launchctl("bootout", f"gui/{uid}", plist_path)
            if os.path.exists(plist_path):
                os.remove(plist_path)
            return True, "已关闭登录自启"
        except OSError as exc:
            return False, str(exc)

    return False, "当前系统暂不支持开机自启"
