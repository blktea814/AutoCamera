import time
import threading
from PyQt6.QtCore import QObject, pyqtSignal
from core.camera import Camera
from core.detector import ProximityDetector
from core.recorder import Recorder


class MonitorSignals(QObject):
    status_changed = pyqtSignal(str)  # "idle" / "monitoring" / "recording"
    frame_ready = pyqtSignal(object)  # numpy frame for preview
    recording_started = pyqtSignal(str)  # file path
    recording_stopped = pyqtSignal(dict)  # recording info dict
    detection_info = pyqtSignal(dict)  # detection result


class Monitor:
    def __init__(self, config: dict):
        self.config = config
        self.signals = MonitorSignals()
        self._camera = Camera(
            camera_index=config["camera_index"],
            resolution=tuple(config["resolution"]),
            fps=config["fps"],
        )
        self._detector = ProximityDetector(
            min_detection_confidence=config["detection_confidence"],
            proximity_threshold=config["proximity_threshold"],
        )
        self._recorder = Recorder(
            save_dir=config["video_save_dir"],
            resolution=tuple(config["resolution"]),
            fps=config["fps"],
        )
        self._running = False
        self._thread = None
        self._frame_skip = config["frame_skip"]
        self._stop_delay = config["stop_delay_seconds"]
        self._last_close_time = None

    def start(self):
        if self._running:
            return
        if not self._camera.open():
            self.signals.status_changed.emit("error")
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        self.signals.status_changed.emit("monitoring")

    def stop(self):
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=3)
            self._thread = None
        if self._recorder.is_recording():
            info = self._recorder.stop()
            if info:
                self.signals.recording_stopped.emit(info)
        self._camera.release()
        self.signals.status_changed.emit("idle")

    def is_running(self) -> bool:
        return self._running

    def set_proximity_threshold(self, value: float):
        self._detector.set_threshold(value)

    def _loop(self):
        frame_count = 0
        while self._running:
            frame = self._camera.read_frame()
            if frame is None:
                time.sleep(0.05)
                continue

            frame_count += 1
            self.signals.frame_ready.emit(frame)

            if self._recorder.is_recording():
                self._recorder.write_frame(frame)

            if frame_count % self._frame_skip != 0:
                continue

            result = self._detector.detect(frame)
            self.signals.detection_info.emit(result)

            if result["close_enough"]:
                self._last_close_time = time.time()
                if not self._recorder.is_recording():
                    file_path = self._recorder.start()
                    self.signals.recording_started.emit(file_path)
                    self.signals.status_changed.emit("recording")
            else:
                if self._recorder.is_recording():
                    if self._last_close_time and (time.time() - self._last_close_time > self._stop_delay):
                        info = self._recorder.stop()
                        if info:
                            self.signals.recording_stopped.emit(info)
                        self.signals.status_changed.emit("monitoring")

            time.sleep(0.01)
