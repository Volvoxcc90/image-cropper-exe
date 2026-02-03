from PySide6.QtWidgets import *
from logic import Logic

class MainWindow(QMainWindow):
    def __init__(self, restart_cb):
        super().__init__()
        self.logic = Logic(self)
        self.restart_cb = restart_cb
        self.setWindowTitle("Image Cropper Pro")
        self.resize(1400, 900)

        bar = self.menuBar()
        ui = bar.addMenu("UI Style")
        for s in ["fluent","material","minimal","studio","saas"]:
            a = QAction(s.capitalize(), self)
            a.triggered.connect(lambda _, x=s: self.change_ui(x))
            ui.addAction(a)

        root = QWidget()
        v = QVBoxLayout(root)
        btn = QPushButton("Открыть папку")
        btn.clicked.connect(self.logic.open_folder)
        v.addWidget(btn)
        v.addWidget(self.logic.view)
        self.setCentralWidget(root)

    def change_ui(self, style):
        self.logic.save_ui_style(style)
        self.restart_cb()
