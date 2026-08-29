import cv2
import os
import time
from datetime import datetime
from typing import Optional


class Recorder:
    def __init__(self, save_dir: str, resolution=(640, 480), fps=20):
        self._save_dir = save_dir
        self._resolution = resolution
        self._fps = fps
        self._writer = None
        self._current_file = None
        self._start_time = None
        os.makedirs(self._save_dir, exist_ok=True)

    def start(self) -> Optional[str]:
        if self._writer is not None:
            return self._current_file

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"record_{timestamp}.mp4"
        self._current_file = os.path.join(self._save_dir, filename)

        frame_size = (self._resolution[0], self._resolution[1])
        for codec in ("avc1", "mp4v"):
            writer = None
            try:
                writer = cv2.VideoWriter(
                    self._current_file,
                    cv2.VideoWriter_fourcc(*codec),
                    self._fps,
                    frame_size,
                )
                if writer.isOpened():
                    self._writer = writer
                    break
            except cv2.error:
                pass
            finally:
                if writer is not None and self._writer is not writer:
                    writer.release()

        if self._writer is None:
            self._current_file = None
            self._start_time = None
            try:
                if os.path.exists(os.path.join(self._save_dir, filename)):
                    os.remove(os.path.join(self._save_dir, filename))
            except OSError:
                pass
            return None

        self._start_time = time.time()
        return self._current_file

    def write_frame(self, frame):
        if self._writer is not None and self._writer.isOpened():
            resized = cv2.resize(frame, (self._resolution[0], self._resolution[1]))
            self._writer.write(resized)

    def stop(self) -> dict:
        if self._writer is None:
            return None
        self._writer.release()
        self._writer = None
        duration = max(0.0, time.time() - self._start_time)
        info = {
            "file_path": self._current_file,
            "start_time": self._start_time,
            "duration": duration,
        }
        self._current_file = None
        self._start_time = None
        return info

    def set_save_dir(self, save_dir: str):
        self._save_dir = save_dir
        os.makedirs(self._save_dir, exist_ok=True)

    def is_recording(self) -> bool:
        return self._writer is not None
