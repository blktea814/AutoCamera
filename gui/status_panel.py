import cv2
import numpy as np
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout
from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtGui import QImage, QPixmap


class StatusPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        self._status_label = QLabel("状态：空闲")
        self._status_label.setStyleSheet("font-size: 16px; font-weight: bold; padding: 8px;")
        layout.addWidget(self._status_label)

        self._preview_label = QLabel()
        self._preview_label.setFixedSize(480, 360)
        self._preview_label.setStyleSheet("background-color: #1a1a2e; border-radius: 8px;")
        self._preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._preview_label.setText("摄像头预览")
        layout.addWidget(self._preview_label, alignment=Qt.AlignmentFlag.AlignCenter)

        info_layout = QHBoxLayout()
        self._ratio_label = QLabel("面积比: --")
        self._detection_label = QLabel("检测: --")
        info_layout.addWidget(self._ratio_label)
        info_layout.addWidget(self._detection_label)
        layout.addLayout(info_layout)

        layout.addStretch()

    @pyqtSlot(object)
    def update_frame(self, frame: np.ndarray):
        if frame is None:
            return
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        bytes_per_line = ch * w
        qimg = QImage(rgb.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(qimg).scaled(
            480, 360, Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self._preview_label.setPixmap(pixmap)

    @pyqtSlot(str)
    def update_status(self, status: str):
        status_map = {
            "idle": "状态：空闲",
            "monitoring": "状态：监控中",
            "recording": "状态：🔴 录制中",
            "error": "状态：⚠ 摄像头错误",
        }
        self._status_label.setText(status_map.get(status, f"状态：{status}"))
        colors = {
            "idle": "#888",
            "monitoring": "#4CAF50",
            "recording": "#F44336",
            "error": "#FF9800",
        }
        color = colors.get(status, "#888")
        self._status_label.setStyleSheet(
            f"font-size: 16px; font-weight: bold; padding: 8px; color: {color};"
        )

    @pyqtSlot(dict)
    def update_detection_info(self, info: dict):
        if info["detected"]:
            self._detection_label.setText("检测: 有人")
            self._ratio_label.setText(f"面积比: {info['ratio']:.4f}")
        else:
            self._detection_label.setText("检测: 无人")
            self._ratio_label.setText("面积比: --")
