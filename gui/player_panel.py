import cv2
import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QSlider
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QImage, QPixmap


class PlayerPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._cap = None
        self._timer = QTimer()
        self._timer.timeout.connect(self._next_frame)
        self._playing = False
        self._total_frames = 0
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        self._title_label = QLabel("录像回放")
        self._title_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(self._title_label)

        self._video_label = QLabel()
        self._video_label.setFixedSize(640, 480)
        self._video_label.setStyleSheet("background-color: #000; border-radius: 4px;")
        self._video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._video_label.setText("选择录像进行播放")
        layout.addWidget(self._video_label, alignment=Qt.AlignmentFlag.AlignCenter)

        self._slider = QSlider(Qt.Orientation.Horizontal)
        self._slider.setEnabled(False)
        self._slider.sliderPressed.connect(self._on_slider_pressed)
        self._slider.sliderReleased.connect(self._on_slider_released)
        layout.addWidget(self._slider)

        ctrl_layout = QHBoxLayout()
        self._btn_play = QPushButton("播放")
        self._btn_play.clicked.connect(self._toggle_play)
        self._btn_play.setEnabled(False)
        ctrl_layout.addWidget(self._btn_play)

        self._btn_stop = QPushButton("停止")
        self._btn_stop.clicked.connect(self._stop)
        self._btn_stop.setEnabled(False)
        ctrl_layout.addWidget(self._btn_stop)

        self._time_label = QLabel("00:00 / 00:00")
        ctrl_layout.addWidget(self._time_label)
        ctrl_layout.addStretch()
        layout.addLayout(ctrl_layout)

        layout.addStretch()

    def load_video(self, file_path: str):
        self._stop()
        self._cap = cv2.VideoCapture(file_path)
        if not self._cap.isOpened():
            self._video_label.setText("无法打开视频文件")
            return
        self._total_frames = int(self._cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self._fps = self._cap.get(cv2.CAP_PROP_FPS) or 20
        self._slider.setRange(0, self._total_frames - 1)
        self._slider.setValue(0)
        self._slider.setEnabled(True)
        self._btn_play.setEnabled(True)
        self._btn_stop.setEnabled(True)
        self._title_label.setText(f"回放: {os.path.basename(file_path)}")
        self._show_frame_at(0)

    def _toggle_play(self):
        if self._playing:
            self._pause()
        else:
            self._play()

    def _play(self):
        if self._cap is None:
            return
        self._playing = True
        self._btn_play.setText("暂停")
        interval = int(1000 / self._fps)
        self._timer.start(interval)

    def _pause(self):
        self._playing = False
        self._btn_play.setText("播放")
        self._timer.stop()

    def _stop(self):
        self._timer.stop()
        self._playing = False
        self._btn_play.setText("播放")
        if self._cap:
            self._cap.release()
            self._cap = None
        self._slider.setValue(0)
        self._slider.setEnabled(False)
        self._btn_play.setEnabled(False)
        self._btn_stop.setEnabled(False)

    def _next_frame(self):
        if self._cap is None:
            return
        ret, frame = self._cap.read()
        if not ret:
            self._pause()
            return
        self._display_frame(frame)
        pos = int(self._cap.get(cv2.CAP_PROP_POS_FRAMES))
        self._slider.setValue(pos)
        self._update_time_label(pos)

    def _show_frame_at(self, pos: int):
        if self._cap is None:
            return
        self._cap.set(cv2.CAP_PROP_POS_FRAMES, pos)
        ret, frame = self._cap.read()
        if ret:
            self._display_frame(frame)
            self._update_time_label(pos)

    def _display_frame(self, frame):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        qimg = QImage(rgb.data, w, h, ch * w, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(qimg).scaled(
            640, 480, Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self._video_label.setPixmap(pixmap)

    def _update_time_label(self, pos: int):
        current_sec = pos / self._fps if self._fps > 0 else 0
        total_sec = self._total_frames / self._fps if self._fps > 0 else 0
        self._time_label.setText(
            f"{int(current_sec//60):02d}:{int(current_sec%60):02d} / "
            f"{int(total_sec//60):02d}:{int(total_sec%60):02d}"
        )

    def _on_slider_pressed(self):
        if self._playing:
            self._timer.stop()

    def _on_slider_released(self):
        pos = self._slider.value()
        self._show_frame_at(pos)
        if self._playing:
            interval = int(1000 / self._fps)
            self._timer.start(interval)
