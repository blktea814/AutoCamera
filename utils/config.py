import json
import os

DEFAULT_CONFIG = {
    "video_save_dir": os.path.join(os.path.expanduser("~"), "CameraMonitor", "recordings"),
    "detection_confidence": 0.5,
    "proximity_threshold": 0.06,
    "stop_delay_seconds": 5,
    "frame_skip": 3,
    "camera_index": 0,
    "resolution": [640, 480],
    "fps": 20,
}

import sys

if getattr(sys, 'frozen', False):
    _base_dir = os.path.dirname(sys.executable)
else:
    _base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CONFIG_PATH = os.path.join(_base_dir, "config.json")


def load_config() -> dict:
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            user_cfg = json.load(f)
        cfg = {**DEFAULT_CONFIG, **user_cfg}
    else:
        cfg = DEFAULT_CONFIG.copy()
        save_config(cfg)
    os.makedirs(cfg["video_save_dir"], exist_ok=True)
    return cfg


def save_config(cfg: dict):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=4, ensure_ascii=False)
