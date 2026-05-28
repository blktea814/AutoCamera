from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QPushButton, QHBoxLayout, QDateEdit, QLabel,
    QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate


class RecordsPanel(QWidget):
    play_requested = pyqtSignal(str)  # file_path
    before_delete = pyqtSignal()  # emitted before any delete to release resources

    def __init__(self, database, parent=None):
        super().__init__(parent)
        self._db = database
        self._init_ui()
        self.refresh()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        filter_layout = QHBoxLayout()
        self._date_edit = QDateEdit(QDate.currentDate())
        self._date_edit.setDisplayFormat("yyyy-MM-dd")
        self._date_edit.setCalendarPopup(True)
        filter_layout.addWidget(QLabel("日期筛选:"))
        filter_layout.addWidget(self._date_edit)

        btn_filter = QPushButton("筛选")
        btn_filter.clicked.connect(self._filter_by_date)
        filter_layout.addWidget(btn_filter)

        btn_all = QPushButton("显示全部")
        btn_all.clicked.connect(self.refresh)
        filter_layout.addWidget(btn_all)

        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        self._table = QTableWidget()
        self._table.setColumnCount(5)
        self._table.setHorizontalHeaderLabels(["ID", "开始时间", "结束时间", "时长(秒)", "操作"])
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self._table)

        delete_layout = QHBoxLayout()
        btn_del_selected = QPushButton("删除选中")
        btn_del_selected.clicked.connect(self._delete_selected)
        delete_layout.addWidget(btn_del_selected)

        btn_del_day = QPushButton("删除当天全部")
        btn_del_day.clicked.connect(self._delete_by_date)
        delete_layout.addWidget(btn_del_day)

        btn_del_all = QPushButton("清空所有记录")
        btn_del_all.clicked.connect(self._delete_all)
        btn_del_all.setStyleSheet("color: red;")
        delete_layout.addWidget(btn_del_all)

        delete_layout.addStretch()
        layout.addLayout(delete_layout)

    def refresh(self):
        events = self._db.get_all_events()
        self._populate_table(events)

    def _filter_by_date(self):
        date_str = self._date_edit.date().toString("yyyy-MM-dd")
        events = self._db.get_events_by_date(date_str)
        self._populate_table(events)

    def _populate_table(self, events: list):
        self._table.setRowCount(len(events))
        for row, ev in enumerate(events):
            self._table.setItem(row, 0, QTableWidgetItem(str(ev["id"])))
            self._table.setItem(row, 1, QTableWidgetItem(ev["start_time"] or ""))
            self._table.setItem(row, 2, QTableWidgetItem(ev["end_time"] or "进行中"))
            duration = f"{ev['duration']:.1f}" if ev["duration"] else "--"
            self._table.setItem(row, 3, QTableWidgetItem(duration))

            btn = QPushButton("播放")
            btn.setEnabled(ev["file_path"] is not None)
            file_path = ev["file_path"]
            btn.clicked.connect(lambda checked, fp=file_path: self.play_requested.emit(fp))
            self._table.setCellWidget(row, 4, btn)

    def _delete_selected(self):
        rows = set(item.row() for item in self._table.selectedItems())
        if not rows:
            QMessageBox.information(self, "提示", "请先选择要删除的记录")
            return
        ids = []
        for row in rows:
            item = self._table.item(row, 0)
            if item:
                ids.append(int(item.text()))
        if not ids:
            return
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定删除选中的 {len(ids)} 条记录及对应录像文件？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.before_delete.emit()
            self._db.delete_events_by_ids(ids)
            self.refresh()

    def _delete_by_date(self):
        date_str = self._date_edit.date().toString("yyyy-MM-dd")
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定删除 {date_str} 的全部记录及对应录像文件？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.before_delete.emit()
            self._db.delete_events_by_date(date_str)
            self.refresh()

    def _delete_all(self):
        reply = QMessageBox.warning(
            self, "确认清空",
            "此操作将删除所有记录和所有录像文件，不可恢复！\n确定继续？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.before_delete.emit()
            self._db.delete_all_events()
            self.refresh()
