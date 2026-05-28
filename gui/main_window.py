import sys
import os
import subprocess
from PyQt6.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QVBoxLayout,
    QSystemTrayIcon, QMenu, QSlider, QLabel, QHBoxLayout,
    QPushButton, QFileDialog, QMessageBox, QCheckBox
)
from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtGui import QIcon, QAction, QPixmap, QPainter, QColor

from gui.status_panel import StatusPanel
from gui.records_panel import RecordsPanel
from gui.player_panel import PlayerPanel
from core.monitor import Monitor
from db.database import Database
from utils.config import load_config, save_config


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._config = load_config()
        self._db = Database()
        self._monitor = Monitor(self._config)
        self._current_event_id = None
        self._init_ui()
        self._connect_signals()
        self._setup_tray()

    def _init_ui(self):
        self.setWindowTitle("AutoCamera")
        self.setMinimumSize(800, 600)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)

        # Control bar
        ctrl_layout = QHBoxLayout()
        self._btn_start = QPushButton("开始监控")
        self._btn_start.clicked.connect(self._toggle_monitor)
        ctrl_layout.addWidget(self._btn_start)

        ctrl_layout.addWidget(QLabel("阈值:"))
        self._threshold_slider = QSlider(Qt.Orientation.Horizontal)
        self._threshold_slider.setRange(3, 15)
        value = int(self._config["proximity_threshold"] * 100)
        self._threshold_slider.setValue(max(3, min(15, value)))
        self._threshold_slider.setFixedWidth(150)
        self._threshold_slider.valueChanged.connect(self._on_threshold_changed)
        ctrl_layout.addWidget(self._threshold_slider)
        self._threshold_label = QLabel(f"{self._config['proximity_threshold']:.2f}")
        ctrl_layout.addWidget(self._threshold_label)

        btn_dir = QPushButton("设置存储目录")
        btn_dir.clicked.connect(self._set_save_dir)
        ctrl_layout.addWidget(btn_dir)

        self._autostart_cb = QCheckBox("开机自启+锁屏运行")
        self._autostart_cb.setChecked(self._is_autostart_enabled())
        self._autostart_cb.stateChanged.connect(self._on_autostart_changed)
        ctrl_layout.addWidget(self._autostart_cb)

        btn_info = QPushButton("i")
        btn_info.setFixedSize(24, 24)
        btn_info.setStyleSheet("font-weight:bold; font-style:italic; border-radius:12px; background:#4CAF50; color:white;")
        btn_info.clicked.connect(self._show_about)
        ctrl_layout.addStretch()
        ctrl_layout.addWidget(btn_info)
        main_layout.addLayout(ctrl_layout)

        # Tabs
        self._tabs = QTabWidget()
        self._status_panel = StatusPanel()
        self._records_panel = RecordsPanel(self._db)
        self._player_panel = PlayerPanel()

        self._tabs.addTab(self._status_panel, "实时监控")
        self._tabs.addTab(self._records_panel, "事件记录")
        self._tabs.addTab(self._player_panel, "录像回放")
        main_layout.addWidget(self._tabs)

    def _connect_signals(self):
        self._monitor.signals.frame_ready.connect(self._status_panel.update_frame)
        self._monitor.signals.status_changed.connect(self._status_panel.update_status)
        self._monitor.signals.detection_info.connect(self._status_panel.update_detection_info)
        self._monitor.signals.recording_started.connect(self._on_recording_started)
        self._monitor.signals.recording_stopped.connect(self._on_recording_stopped)
        self._records_panel.play_requested.connect(self._play_video)
        self._records_panel.before_delete.connect(self._player_panel._stop)

    def _create_icon(self):
        pixmap = QPixmap(64, 64)
        pixmap.fill(QColor(0, 0, 0, 0))
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QColor(76, 175, 80))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(4, 4, 56, 56)
        painter.setBrush(QColor(255, 255, 255))
        painter.drawEllipse(18, 18, 28, 28)
        painter.setBrush(QColor(33, 33, 33))
        painter.drawEllipse(24, 24, 16, 16)
        painter.end()
        return QIcon(pixmap)

    def _setup_tray(self):
        icon = self._create_icon()
        self.setWindowIcon(icon)
        self._tray = QSystemTrayIcon(self)
        self._tray.setIcon(icon)
        self._tray.setToolTip("摄像头监控")

        tray_menu = QMenu()
        action_show = QAction("显示主窗口", self)
        action_show.triggered.connect(self.show)
        tray_menu.addAction(action_show)

        self._tray_monitor_action = QAction("开始监控", self)
        self._tray_monitor_action.triggered.connect(self._toggle_monitor)
        tray_menu.addAction(self._tray_monitor_action)

        tray_menu.addSeparator()
        action_quit = QAction("退出", self)
        action_quit.triggered.connect(self._quit_app)
        tray_menu.addAction(action_quit)

        self._tray.setContextMenu(tray_menu)
        self._tray.activated.connect(self._on_tray_activated)
        self._tray.show()

    def auto_start_monitor(self):
        self._monitor.start()
        self._btn_start.setText("停止监控")
        self._tray_monitor_action.setText("停止监控")

    def _toggle_monitor(self):
        if self._monitor.is_running():
            self._monitor.stop()
            self._btn_start.setText("开始监控")
            self._tray_monitor_action.setText("开始监控")
        else:
            self._monitor.start()
            self._btn_start.setText("停止监控")
            self._tray_monitor_action.setText("停止监控")

    def _on_threshold_changed(self, value):
        threshold = value / 100.0
        self._threshold_label.setText(f"{threshold:.2f}")
        self._monitor.set_proximity_threshold(threshold)
        self._config["proximity_threshold"] = threshold
        save_config(self._config)

    def _set_save_dir(self):
        dir_path = QFileDialog.getExistingDirectory(self, "选择录像存储目录")
        if dir_path:
            self._config["video_save_dir"] = dir_path
            save_config(self._config)
            self._monitor._recorder.set_save_dir(dir_path)
            QMessageBox.information(self, "设置成功", f"录像将保存到:\n{dir_path}")

    @pyqtSlot(str)
    def _on_recording_started(self, file_path: str):
        import time
        self._current_event_id = self._db.add_event(time.time(), file_path)

    @pyqtSlot(dict)
    def _on_recording_stopped(self, info: dict):
        if self._current_event_id:
            self._db.finish_event(self._current_event_id, info["duration"])
            self._current_event_id = None
        self._records_panel.refresh()

    def _play_video(self, file_path: str):
        self._tabs.setCurrentWidget(self._player_panel)
        self._player_panel.load_video(file_path)

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show()
            self.activateWindow()

    def closeEvent(self, event):
        event.ignore()
        self.hide()
        self._tray.showMessage("摄像头监控", "程序已最小化到托盘，继续后台运行", QSystemTrayIcon.MessageIcon.Information)

    def _get_exe_path(self) -> str:
        if getattr(sys, 'frozen', False):
            return sys.executable
        return os.path.abspath(os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 'dist', 'AutoCamera.exe'
        ))

    def _is_autostart_enabled(self) -> bool:
        try:
            result = subprocess.run(
                ['schtasks', '/query', '/tn', 'AutoCamera'],
                capture_output=True, text=True, creationflags=0x08000000
            )
            return result.returncode == 0
        except Exception:
            return False

    def _on_autostart_changed(self, state):
        if state == 2:  # checked
            exe_path = self._get_exe_path()
            if not os.path.exists(exe_path) and not getattr(sys, 'frozen', False):
                QMessageBox.warning(self, "提示",
                    "未找到 AutoCamera.exe\n请先运行 build.py 打包后再启用此功能")
                self._autostart_cb.setChecked(False)
                return
            try:
                result = subprocess.run(
                    ['schtasks', '/create', '/tn', 'AutoCamera',
                     '/tr', f'\"{exe_path}\" --background',
                     '/sc', 'onlogon', '/rl', 'highest', '/f'],
                    capture_output=True, text=True, creationflags=0x08000000
                )
                if result.returncode == 0:
                    QMessageBox.information(self, "成功", "已启用开机自启和锁屏运行")
                else:
                    QMessageBox.warning(self, "失败",
                        f"需要管理员权限，请以管理员身份运行程序\n{result.stderr}")
                    self._autostart_cb.setChecked(False)
            except Exception as e:
                QMessageBox.warning(self, "错误", str(e))
                self._autostart_cb.setChecked(False)
        else:  # unchecked
            try:
                subprocess.run(
                    ['schtasks', '/delete', '/tn', 'AutoCamera', '/f'],
                    capture_output=True, text=True, creationflags=0x08000000
                )
                QMessageBox.information(self, "成功", "已关闭开机自启")
            except Exception:
                pass

    def _show_about(self):
        QMessageBox.about(self, "关于 AutoCamera",
            "by BLKTEA\n小黑盒ID：68344144")

    def _quit_app(self):
        self._monitor.stop()
        self._db.close()
        self._tray.hide()
        from PyQt6.QtWidgets import QApplication
        QApplication.quit()
