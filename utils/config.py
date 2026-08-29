import json
import os
import ntpath
import shutil
import sys
from utils.paths import config_path, default_video_dir

DEFAULT_CONFIG = {
    "video_save_dir": default_video_dir(),
    "detection_confidence": 0.5,
    "proximity_threshold": 0.06,
    "stop_delay_seconds": 5,
    "frame_skip": 3,
    "camera_index": 0,
    "resolution": [640, 480],
    "fps": 20,
}

CONFIG_PATH = config_path()


def _default_config() -> dict:
    cfg = DEFAULT_CONFIG.copy()
    cfg["resolution"] = list(DEFAULT_CONFIG["resolution"])
    return cfg


def _resolve_video_dir(path: str) -> str:
    if not isinstance(path, str):
        return DEFAULT_CONFIG["video_save_dir"]
    path = os.path.expanduser(os.path.expandvars(path or ""))
    # The repository ships with a Windows example path. Do not create a
    # directory containing backslashes when that config is first used on macOS.
    if os.name != "nt" and (ntpath.splitdrive(path)[0] or "\\" in path):
        return DEFAULT_CONFIG["video_save_dir"]
    return path or DEFAULT_CONFIG["video_save_dir"]


def _bundled_config_path() -> str:
    bundle_root = getattr(sys, "_MEIPASS", None)
    if bundle_root:
        return os.path.join(bundle_root, "config.json")
    return os.path.join(os.path.dirname(CONFIG_PATH), "config.json")


def _backup_invalid_config():
    backup_path = f"{CONFIG_PATH}.bak"
    try:
        shutil.copy2(CONFIG_PATH, backup_path)
    except OSError:
        pass


def _validated_config(user_cfg: dict) -> dict:
    cfg = {**_default_config(), **user_cfg}

    cfg["video_save_dir"] = _resolve_video_dir(cfg.get("video_save_dir"))

    try:
        confidence = float(cfg["detection_confidence"])
        cfg["detection_confidence"] = confidence if 0.0 <= confidence <= 1.0 else DEFAULT_CONFIG["detection_confidence"]
    except (TypeError, ValueError):
        cfg["detection_confidence"] = DEFAULT_CONFIG["detection_confidence"]

    try:
        threshold = float(cfg["proximity_threshold"])
        cfg["proximity_threshold"] = threshold if 0.0 < threshold <= 1.0 else DEFAULT_CONFIG["proximity_threshold"]
    except (TypeError, ValueError):
        cfg["proximity_threshold"] = DEFAULT_CONFIG["proximity_threshold"]

    try:
        stop_delay = float(cfg["stop_delay_seconds"])
        cfg["stop_delay_seconds"] = max(0.0, stop_delay)
    except (TypeError, ValueError):
        cfg["stop_delay_seconds"] = DEFAULT_CONFIG["stop_delay_seconds"]

    try:
        cfg["frame_skip"] = max(1, int(cfg["frame_skip"]))
    except (TypeError, ValueError):
        cfg["frame_skip"] = DEFAULT_CONFIG["frame_skip"]

    try:
        cfg["camera_index"] = max(0, int(cfg["camera_index"]))
    except (TypeError, ValueError):
        cfg["camera_index"] = DEFAULT_CONFIG["camera_index"]

    resolution = cfg.get("resolution")
    if not isinstance(resolution, (list, tuple)) or len(resolution) != 2:
        resolution = DEFAULT_CONFIG["resolution"]
    try:
        width, height = (int(resolution[0]), int(resolution[1]))
        cfg["resolution"] = [width, height] if width > 0 and height > 0 else list(DEFAULT_CONFIG["resolution"])
    except (TypeError, ValueError):
        cfg["resolution"] = list(DEFAULT_CONFIG["resolution"])

    try:
        fps = float(cfg["fps"])
        cfg["fps"] = fps if fps > 0 else DEFAULT_CONFIG["fps"]
    except (TypeError, ValueError):
        cfg["fps"] = DEFAULT_CONFIG["fps"]

    return cfg


def load_config() -> dict:
    user_cfg = None
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            if isinstance(loaded, dict):
                user_cfg = loaded
        except (OSError, json.JSONDecodeError, TypeError):
            _backup_invalid_config()

    if user_cfg is None:
        bundled_path = _bundled_config_path()
        if bundled_path != CONFIG_PATH and os.path.exists(bundled_path):
            try:
                with open(bundled_path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                if isinstance(loaded, dict):
                    user_cfg = loaded
            except (OSError, json.JSONDecodeError, TypeError):
                user_cfg = None

    cfg = _validated_config(user_cfg or {})
    if not os.path.exists(CONFIG_PATH) or user_cfg is None:
        save_config(cfg)
    os.makedirs(cfg["video_save_dir"], exist_ok=True)
    return cfg


def save_config(cfg: dict):
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    temp_path = f"{CONFIG_PATH}.tmp"
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=4, ensure_ascii=False)
    os.replace(temp_path, CONFIG_PATH)
