#!/usr/bin/env python3
# users_app_pyqt6.py — PyQt6 version of the users table viewer

from typing import List
from PyQt6.QtCore import QAbstractTableModel, QModelIndex, Qt, QVariant
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QTableView, QPushButton, QHBoxLayout, QMessageBox, QAbstractItemView
)

from user_dao import UserDAO, User


class UserTableModel(QAbstractTableModel):
    HEADERS = ["ID", "Name", "Email", "Active"]

    def __init__(self, users: List[User]) -> None:
        super().__init__()
        self._users = users

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._users)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 4

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return QVariant()

        user = self._users[index.row()]
        col = index.column()

        if role == Qt.ItemDataRole.DisplayRole:
            if col == 0: return user.id
            if col == 1: return user.name
            if col == 2: return user.email or ""
            if col == 3: return "True" if user.active else "False"

        if role == Qt.ItemDataRole.TextAlignmentRole:
            if col in (0, 3):
                return Qt.AlignmentFlag.AlignCenter
            return Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter

        return QVariant()

    def headerData(self, section: int, orientation: Qt.Orientation,
                   role: int = Qt.ItemDataRole.DisplayRole):
        if role != Qt.ItemDataRole.DisplayRole:
            return QVariant()
        if orientation == Qt.Orientation.Horizontal:
            return self.HEADERS[section]
        return section + 1  # row numbers

    def set_users(self, users: List[User]) -> None:
        self.beginResetModel()
        self._users = users
        self.endResetModel()


class MainWindow(QMainWindow):
    def __init__(self, db_path: str = "users.db") -> None:
        super().__init__()
        self.setWindowTitle("Users - SQLite Viewer (PyQt6)")

        self.dao = UserDAO(db_path)
        self.dao.create_table()  # safe if exists

        central = QWidget(self)
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        self.table = QTableView(self)
        self.table.setSortingEnabled(True)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        layout.addWidget(self.table)

        btns = QHBoxLayout()
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.load_users)
        btns.addWidget(self.refresh_btn)
        btns.addStretch(1)
        layout.addLayout(btns)

        self.load_users()

        self.resize(800, 400)
        self.table.resizeColumnsToContents()
        self.table.horizontalHeader().setStretchLastSection(True)

    def load_users(self) -> None:
        try:
            users = self.dao.get_all()
            if not hasattr(self, "model"):
                self.model = UserTableModel(users)
                self.table.setModel(self.model)
            else:
                self.model.set_users(users)
            self.statusBar().showMessage(f"Loaded {len(users)} users", 3000)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load users:\n{e}")


def main():
    import sys
    app = QApplication(sys.argv)
    win = MainWindow("users.db")
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
