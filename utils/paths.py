import os
import sys


APP_NAME = "AutoCamera"
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def app_data_dir() -> str:
    """Return a writable directory for application state.

    A macOS app bundle is not a writable location, so packaged macOS builds
    keep their config, database and logs in Application Support.  The
    original Windows behavior (next to the executable) is preserved.
    """
    if getattr(sys, "frozen", False):
        if sys.platform == "darwin":
            return os.path.join(os.path.expanduser("~"), "Library", "Application Support", APP_NAME)
        return os.path.dirname(os.path.abspath(sys.executable))
    return PROJECT_ROOT


def default_video_dir() -> str:
    return os.path.join(os.path.expanduser("~"), "CameraMonitor", "recordings")


def config_path() -> str:
    return os.path.join(app_data_dir(), "config.json")


def database_path() -> str:
    return os.path.join(app_data_dir(), "events.db")
