import sys, os
from PIL import Image, ImageEnhance
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QFileDialog, QLabel, QLineEdit, QMessageBox,
    QGraphicsView, QGraphicsScene
)
from PySide6.QtGui import QPixmap
from PySide6.QtCore import QRectF, Qt


class ZoomView(QGraphicsView):
    def wheelEvent(self, event):
        if event.modifiers() & Qt.ControlModifier:
            factor = 1.15 if event.angleDelta().y() > 0 else 0.87
            self.scale(factor, factor)
        else:
            super().wheelEvent(event)


class App(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Image Cropper Pro")
        self.resize(1400, 900)

        self.images = []
        self.index = 0
        self.rects = []
        self.current_image = None

        self.scene = QGraphicsScene()
        self.view = ZoomView(self.scene)

        self._ui()

    def _ui(self):
        root = QWidget()
        layout = QVBoxLayout(root)

        top = QHBoxLayout()

        btn_open = QPushButton("📂 Открыть папку")
        btn_prev = QPushButton("⬅")
        btn_next = QPushButton("➡")
        btn_add = QPushButton("+ Зона")
        btn_del = QPushButton("🗑 Удалить")
        btn_process = QPushButton("▶ Обработать лист")

        self.w_edit = QLineEdit("1200")
        self.h_edit = QLineEdit("1700")
        self.info = QLabel("0 / 0")

        for w in [btn_open, btn_prev, btn_next, btn_add, btn_del,
                  QLabel("W:"), self.w_edit,
                  QLabel("H:"), self.h_edit,
                  btn_process, self.info]:
            top.addWidget(w)

        layout.addLayout(top)
        layout.addWidget(self.view)
        self.setCentralWidget(root)

        btn_open.clicked.connect(self.open_folder)
        btn_prev.clicked.connect(self.prev_image)
        btn_next.clicked.connect(self.next_image)
        btn_add.clicked.connect(self.add_rect)
        btn_del.clicked.connect(self.delete_rect)
        btn_process.clicked.connect(self.process_current)

        self.setStyleSheet("""
            QMainWindow { background:#1e1e1e; color:white; }
            QPushButton {
                background:#2b2b2b;
                border-radius:6px;
                padding:6px 10px;
            }
            QPushButton:hover { background:#3a3a3a; }
            QLineEdit {
                background:#111;
                color:white;
                padding:4px;
                border-radius:4px;
                width:60px;
            }
        """)

    # ---------- Работа с изображениями ----------

    def open_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Папка с листами")
        if not folder:
            return

        self.images = [
            os.path.join(folder, f)
            for f in os.listdir(folder)
            if f.lower().endswith((".jpg", ".png", ".jpeg"))
        ]
        if not self.images:
            QMessageBox.warning(self, "Ошибка", "Нет изображений")
            return

        self.index = 0
        self.load_image()

    def load_image(self):
        self.scene.clear()
        self.rects.clear()

        path = self.images[self.index]
        self.current_image = Image.open(path).convert("RGB")

        pix = QPixmap(path)
        self.scene.addPixmap(pix)

        self.info.setText(f"{self.index+1} / {len(self.images)}")

    def next_image(self):
        if self.index < len(self.images) - 1:
            self.index += 1
            self.load_image()

    def prev_image(self):
        if self.index > 0:
            self.index -= 1
            self.load_image()

    # ---------- Зоны ----------

    def add_rect(self):
        r = self.scene.addRect(QRectF(50, 50, 300, 400))
        r.setFlag(r.ItemIsMovable, True)
        r.setFlag(r.ItemIsSelectable, True)
        self.rects.append(r)

    def delete_rect(self):
        for r in self.rects[:]:
            if r.isSelected():
                self.scene.removeItem(r)
                self.rects.remove(r)

    # ---------- Обработка ----------

    def process_current(self):
        if not self.rects:
            QMessageBox.warning(self, "Ошибка", "Нет зон")
            return

        try:
            tw = int(self.w_edit.text())
            th = int(self.h_edit.text())
        except ValueError:
            QMessageBox.warning(self, "Ошибка", "Неверный размер")
            return

        name = os.path.splitext(os.path.basename(self.images[self.index]))[0]
        out_dir = os.path.join("output", name)
        os.makedirs(out_dir, exist_ok=True)

        for i, r in enumerate(self.rects, 1):
            b = r.sceneBoundingRect()
            crop = self.current_image.crop(
                (int(b.left()), int(b.top()), int(b.right()), int(b.bottom()))
            )

            crop = crop.resize((tw, th), Image.LANCZOS)
            crop = ImageEnhance.Contrast(crop).enhance(1.08)
            crop = ImageEnhance.Brightness(crop).enhance(1.02)
            crop = ImageEnhance.Sharpness(crop).enhance(1.25)

            crop.save(
                os.path.join(out_dir, f"{i}.jpg"),
                quality=95,
                subsampling=0
            )

        QMessageBox.information(self, "Готово", out_dir)


def main():
    app = QApplication(sys.argv)
    w = App()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
