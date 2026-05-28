"""
后台无GUI服务模式 - 用于锁屏时持续运行
使用方法: pythonw.exe service.py
或通过 Windows 任务计划程序设置开机自启
"""
import sys
import os
import time
import signal

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.camera import Camera
from core.detector import ProximityDetector
from core.recorder import Recorder
from db.database import Database
from utils.config import load_config


class BackgroundService:
    def __init__(self):
        self._config = load_config()
        self._camera = Camera(
            camera_index=self._config["camera_index"],
            resolution=tuple(self._config["resolution"]),
            fps=self._config["fps"],
        )
        self._detector = ProximityDetector(
            min_detection_confidence=self._config["detection_confidence"],
            proximity_threshold=self._config["proximity_threshold"],
        )
        self._recorder = Recorder(
            save_dir=self._config["video_save_dir"],
            resolution=tuple(self._config["resolution"]),
            fps=self._config["fps"],
        )
        self._db = Database()
        self._running = False
        self._current_event_id = None

    def start(self):
        if not self._camera.open():
            self._log("ERROR: Cannot open camera")
            return
        self._running = True
        self._log("Service started")
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        self._run_loop()

    def _run_loop(self):
        frame_count = 0
        last_close_time = None
        stop_delay = self._config["stop_delay_seconds"]
        frame_skip = self._config["frame_skip"]

        while self._running:
            frame = self._camera.read_frame()
            if frame is None:
                time.sleep(0.1)
                continue

            frame_count += 1

            if self._recorder.is_recording():
                self._recorder.write_frame(frame)

            if frame_count % frame_skip != 0:
                time.sleep(0.01)
                continue

            result = self._detector.detect(frame)

            if result["close_enough"]:
                last_close_time = time.time()
                if not self._recorder.is_recording():
                    file_path = self._recorder.start()
                    self._current_event_id = self._db.add_event(time.time(), file_path)
                    self._log(f"Recording started: {file_path}")
            else:
                if self._recorder.is_recording():
                    if last_close_time and (time.time() - last_close_time > stop_delay):
                        info = self._recorder.stop()
                        if info and self._current_event_id:
                            self._db.finish_event(self._current_event_id, info["duration"])
                            self._log(f"Recording stopped: {info['duration']:.1f}s")
                        self._current_event_id = None

            time.sleep(0.01)

    def stop(self):
        self._running = False
        if self._recorder.is_recording():
            info = self._recorder.stop()
            if info and self._current_event_id:
                self._db.finish_event(self._current_event_id, info["duration"])
        self._camera.release()
        self._detector.release()
        self._db.close()
        self._log("Service stopped")

    def _signal_handler(self, signum, frame):
        self.stop()

    def _log(self, msg: str):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"[{timestamp}] {msg}\n"
        log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "service.log")
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(log_line)


if __name__ == "__main__":
    service = BackgroundService()
    try:
        service.start()
    except Exception as e:
        service._log(f"Fatal error: {e}")
        service.stop()
