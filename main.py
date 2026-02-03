import sys, os
from PIL import Image, ImageEnhance
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QFileDialog, QLabel, QLineEdit, QMessageBox,
    QGraphicsView, QGraphicsScene, QGraphicsRectItem
)
from PySide6.QtGui import QPixmap, QPen, QColor
from PySide6.QtCore import QRectF, Qt


# ================= Graphics View с рисованием зон =================

class CropView(QGraphicsView):
    def __init__(self, scene, app):
        super().__init__(scene)
        self.app = app
        self.drawing = False
        self.start_pos = None
        self.temp_rect = None

        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)

    def wheelEvent(self, event):
        if event.modifiers() & Qt.ControlModifier:
            factor = 1.15 if event.angleDelta().y() > 0 else 0.87
            self.scale(factor, factor)
        else:
            super().wheelEvent(event)

    def mousePressEvent(self, event):
        if self.app.draw_mode and event.button() == Qt.LeftButton:
            self.drawing = True
            self.start_pos = self.mapToScene(event.pos())
            self.temp_rect = QGraphicsRectItem(QRectF(self.start_pos, self.start_pos))
            self.temp_rect.setPen(QPen(QColor(0, 180, 255), 2))
            self.scene().addItem(self.temp_rect)
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.drawing and self.temp_rect:
            current_pos = self.mapToScene(event.pos())
            rect = QRectF(self.start_pos, current_pos).normalized()
            self.temp_rect.setRect(rect)
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.drawing and self.temp_rect:
            rect = self.temp_rect.rect()
            self.scene().removeItem(self.temp_rect)

            if rect.width() > 10 and rect.height() > 10:
                final_rect = QGraphicsRectItem(rect)
                final_rect.setPen(QPen(QColor(255, 180, 0), 2))
                final_rect.setFlag(QGraphicsRectItem.ItemIsMovable, True)
                final_rect.setFlag(QGraphicsRectItem.ItemIsSelectable, True)
                self.scene().addItem(final_rect)
                self.app.rects.append(final_rect)

            self.temp_rect = None
            self.drawing = False
        else:
            super().mouseReleaseEvent(event)


# ================= Главное приложение =================

class App(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Image Cropper Pro")
        self.resize(1400, 900)

        self.images = []
        self.index = 0
        self.rects = []
        self.current_image = None
        self.draw_mode = False

        self.scene = QGraphicsScene()
        self.view = CropView(self.scene, self)

        self._build_ui()

    def _build_ui(self):
        root = QWidget()
        layout = QVBoxLayout(root)

        top = QHBoxLayout()

        btn_open = QPushButton("📂 Открыть папку")
        btn_prev = QPushButton("⬅")
        btn_next = QPushButton("➡")
        btn_draw = QPushButton("+ Зона (рисовать)")
        btn_del = QPushButton("🗑 Удалить зону")
        btn_process = QPushButton("▶ Обработать лист")

        self.w_edit = QLineEdit("1200")
        self.h_edit = QLineEdit("1700")
        self.info = QLabel("0 / 0")

        for w in [
            btn_open, btn_prev, btn_next, btn_draw, btn_del,
            QLabel("W:"), self.w_edit,
            QLabel("H:"), self.h_edit,
            btn_process, self.info
        ]:
            top.addWidget(w)

        layout.addLayout(top)
        layout.addWidget(self.view)
        self.setCentralWidget(root)

        btn_open.clicked.connect(self.open_folder)
        btn_prev.clicked.connect(self.prev_image)
        btn_next.clicked.connect(self.next_image)
        btn_draw.clicked.connect(self.toggle_draw_mode)
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
                width:70px;
            }
        """)

    # ================= Работа с изображениями =================

    def open_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Папка с листами")
        if not folder:
            return

        self.images = [
            os.path.join(folder, f)
            for f in os.listdir(folder)
            if f.lower().endswith((".jpg", ".jpeg", ".png"))
        ]

        if not self.images:
            QMessageBox.warning(self, "Ошибка", "В папке нет изображений")
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

        self.view.fitInView(self.scene.itemsBoundingRect(), Qt.KeepAspectRatio)
        self.info.setText(f"{self.index + 1} / {len(self.images)}")

    def next_image(self):
        if self.index < len(self.images) - 1:
            self.index += 1
            self.load_image()

    def prev_image(self):
        if self.index > 0:
            self.index -= 1
            self.load_image()

    # ================= Зоны =================

    def toggle_draw_mode(self):
        self.draw_mode = not self.draw_mode

    def delete_rect(self):
        for r in self.rects[:]:
            if r.isSelected():
                self.scene.removeItem(r)
                self.rects.remove(r)

    # ================= Обработка =================

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

            crop = self.current_image.crop((
                int(b.left()),
                int(b.top()),
                int(b.right()),
                int(b.bottom())
            ))

            # 🔥 качественный ресайз
            crop = crop.resize((tw, th), Image.LANCZOS)

            # 🔥 ЗАМЕТНОЕ улучшение
            crop = ImageEnhance.Contrast(crop).enhance(1.18)
            crop = ImageEnhance.Brightness(crop).enhance(1.04)
            crop = ImageEnhance.Sharpness(crop).enhance(1.6)

            crop.save(
                os.path.join(out_dir, f"{i}.jpg"),
                quality=95,
                subsampling=0
            )

        QMessageBox.information(
            self,
            "Готово",
            f"Сохранено в папку:\n{out_dir}"
        )


# ================= Запуск =================

def main():
    app = QApplication(sys.argv)
    win = App()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
