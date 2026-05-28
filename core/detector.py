import mediapipe as mp
import numpy as np


class ProximityDetector:
    def __init__(self, min_detection_confidence=0.5, proximity_threshold=0.03):
        self._proximity_threshold = proximity_threshold
        self._face_detection = mp.solutions.face_detection.FaceDetection(
            model_selection=0,
            min_detection_confidence=min_detection_confidence,
        )

    def detect(self, frame: np.ndarray) -> dict:
        h, w, _ = frame.shape
        frame_area = h * w
        rgb = frame[:, :, ::-1]
        results = self._face_detection.process(rgb)

        if not results.detections:
            return {"detected": False, "close_enough": False, "ratio": 0.0, "bbox": None}

        max_ratio = 0.0
        max_bbox = None
        for detection in results.detections:
            bb = detection.location_data.relative_bounding_box
            face_area = bb.width * bb.height
            if face_area > max_ratio:
                max_ratio = face_area
                max_bbox = (bb.xmin, bb.ymin, bb.width, bb.height)

        close_enough = max_ratio >= self._proximity_threshold
        return {
            "detected": True,
            "close_enough": close_enough,
            "ratio": max_ratio,
            "bbox": max_bbox,
        }

    def set_threshold(self, threshold: float):
        self._proximity_threshold = threshold

    def release(self):
        self._face_detection.close()
