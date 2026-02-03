from PySide6.QtWidgets import *
from PySide6.QtCore import Qt
from logic import Logic

class MainWindow(QMainWindow):
    def __init__(self, restart_cb):
        super().__init__()
        self.restart_cb = restart_cb
        self.logic = Logic(self)

        self.setWindowTitle("Image Cropper Pro")
        self.resize(1400, 900)

        self._menu()
        self._ui()
        self.setStyleSheet("""
            QMainWindow { background: #1e1e1e; }
            QPushButton {
                background: #2b2b2b;
                border-radius: 8px;
                padding: 8px 14px;
            }
            QPushButton:hover { background: #3a3a3a; }
        """)

    def _menu(self):
        bar = self.menuBar()
        ui = bar.addMenu("UI Style")
        for s in ["fluent","material","minimal","studio","saas"]:
            a = QAction(s.capitalize(), self)
            a.triggered.connect(lambda _, x=s: self.change_ui(x))
            ui.addAction(a)

    def _ui(self):
        root = QWidget()
        v = QVBoxLayout(root)

        top = QHBoxLayout()
        for text, fn in [
            ("📂 Открыть папку", self.logic.open_folder),
            ("➕ Зона", self.logic.add_zone),
            ("🗑 Удалить", self.logic.delete_zone),
            ("👁 Предпросмотр", self.logic.preview),
            ("▶ Обработать лист", self.logic.process_current),
        ]:
            b = QPushButton(text)
            b.clicked.connect(fn)
            top.addWidget(b)

        top.addStretch()
        v.addLayout(top)
        v.addWidget(self.logic.view)
        self.setCentralWidget(root)

    def change_ui(self, style):
        self.logic.save_ui_style(style)
        self.restart_cb()
