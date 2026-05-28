import cv2
import threading


class Camera:
    def __init__(self, camera_index=0, resolution=(640, 480), fps=20):
        self._index = camera_index
        self._resolution = resolution
        self._fps = fps
        self._cap = None
        self._lock = threading.Lock()

    def open(self) -> bool:
        with self._lock:
            self._cap = cv2.VideoCapture(self._index, cv2.CAP_DSHOW)
            if not self._cap.isOpened():
                return False
            self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self._resolution[0])
            self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self._resolution[1])
            self._cap.set(cv2.CAP_PROP_FPS, self._fps)
            return True

    def read_frame(self):
        with self._lock:
            if self._cap is None or not self._cap.isOpened():
                return None
            ret, frame = self._cap.read()
            return frame if ret else None

    def is_opened(self) -> bool:
        with self._lock:
            return self._cap is not None and self._cap.isOpened()

    def get_resolution(self) -> tuple:
        return self._resolution

    def get_fps(self) -> int:
        return self._fps

    def release(self):
        with self._lock:
            if self._cap is not None:
                self._cap.release()
                self._cap = None
