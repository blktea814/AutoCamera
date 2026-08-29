import json
import os
import ntpath
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


def _resolve_video_dir(path: str) -> str:
    path = os.path.expanduser(os.path.expandvars(path or ""))
    # The repository ships with a Windows example path. Do not create a
    # directory containing backslashes when that config is first used on macOS.
    if os.name != "nt" and (ntpath.splitdrive(path)[0] or "\\" in path):
        return DEFAULT_CONFIG["video_save_dir"]
    return path or DEFAULT_CONFIG["video_save_dir"]


def load_config() -> dict:
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            user_cfg = json.load(f)
        cfg = {**DEFAULT_CONFIG, **user_cfg}
    else:
        cfg = DEFAULT_CONFIG.copy()
        save_config(cfg)
    cfg["video_save_dir"] = _resolve_video_dir(cfg["video_save_dir"])
    os.makedirs(cfg["video_save_dir"], exist_ok=True)
    return cfg


def save_config(cfg: dict):
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=4, ensure_ascii=False)
