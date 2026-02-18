# Watermarkly‑style Crop Tool (Rect + Circle) + Clean UI
# pip install PySide6 Pillow opencv-python numpy

import sys, os
import numpy as np
import cv2
from PIL import Image, ImageDraw

try:
    from PySide6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
        QPushButton, QFileDialog, QLabel, QCheckBox, QSpinBox,
        QGraphicsView, QGraphicsScene, QGraphicsRectItem,
        QMessageBox
    )
    from PySide6.QtGui import QPixmap, QColor, QPen, QPainterPath
    from PySide6.QtCore import Qt, QRectF
except ModuleNotFoundError:
    print("Install: pip install PySide6 Pillow opencv-python numpy")
    sys.exit(1)


# ---------------- OpenCV Enhance ----------------
def enhance_image_opencv(pil_img):
    img = np.array(pil_img)
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

    blur = cv2.GaussianBlur(img, (0, 0), 1.2)
    sharp = cv2.addWeighted(img, 1.4, blur, -0.4, 0)

    lab = cv2.cvtColor(sharp, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l = clahe.apply(l)
    lab = cv2.merge((l, a, b))
    final = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)

    return Image.fromarray(final)


# ---------------- Canvas ----------------
class Canvas(QGraphicsView):
    def __init__(self, scene, app):
        super().__init__(scene)
        self.app = app
        self.start_pos = None
        self.temp_item = None
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setStyleSheet("background:#1e1e1e;")

    def wheelEvent(self, e):
        if e.modifiers() & Qt.ControlModifier:
            factor = 1.15 if e.angleDelta().y() > 0 else 0.87
            self.scale(factor, factor)
        else:
            super().wheelEvent(e)

    def mousePressEvent(self, e):
        if self.app.crop_mode and e.button() == Qt.LeftButton:
            self.start_pos = self.mapToScene(e.pos())
            self.temp_item = QGraphicsRectItem(QRectF(self.start_pos, self.start_pos))
            self.temp_item.setPen(QPen(QColor("#00c8ff"), 2, Qt.DashLine))
            self.scene().addItem(self.temp_item)
        else:
            super().mousePressEvent(e)

    def mouseMoveEvent(self, e):
        if self.temp_item:
            rect = QRectF(self.start_pos, self.mapToScene(e.pos())).normalized()
            self.temp_item.setRect(rect)
        else:
            super().mouseMoveEvent(e)

    def mouseReleaseEvent(self, e):
        if self.temp_item:
            rect = self.temp_item.rect()
            self.scene().removeItem(self.temp_item)
            if rect.width() > 20 and rect.height() > 20:
                r = QGraphicsRectItem(rect)
                r.setPen(QPen(QColor("#ffb400"), 2))
                r.setFlag(QGraphicsRectItem.ItemIsMovable, True)
                r.setFlag(QGraphicsRectItem.ItemIsSelectable, True)
                self.scene().addItem(r)
                self.app.crop_rects.append(r)
            self.temp_item = None
        else:
            super().mouseReleaseEvent(e)


# ---------------- Main Window ----------------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Watermarkly‑Style Crop Pro")
        self.resize(1500, 900)
        self.setStyleSheet("""
            QMainWindow { background:#f4f6f8; }
            QPushButton {
                background:#0066ff;
                color:white;
                border-radius:6px;
                padding:6px;
            }
            QPushButton:hover { background:#0052cc; }
        """)

        self.scene = QGraphicsScene()
        self.canvas = Canvas(self.scene, self)

        self.images = []
        self.index = 0
        self.base_image = None
        self.crop_rects = []
        self.crop_mode = False

        # Modes
        self.circle_mode = QCheckBox("Circle Crop")
        self.resize_check = QCheckBox("Resize")
        self.enhance_check = QCheckBox("Enhance")

        self.w_edit = QSpinBox(); self.w_edit.setRange(100, 4000); self.w_edit.setValue(1200)
        self.h_edit = QSpinBox(); self.h_edit.setRange(100, 4000); self.h_edit.setValue(1200)

        btn_open = QPushButton("Open Images Folder")
        btn_open.clicked.connect(self.open_folder)

        btn_crop = QPushButton("Toggle Crop Mode")
        btn_crop.clicked.connect(lambda: setattr(self, 'crop_mode', not self.crop_mode))

        btn_process = QPushButton("Export PNG")
        btn_process.clicked.connect(self.process_images)

        side = QVBoxLayout()
        for w in [btn_open, btn_crop,
                  self.circle_mode,
                  self.resize_check, QLabel("Width"), self.w_edit,
                  QLabel("Height"), self.h_edit,
                  self.enhance_check,
                  btn_process]:
            side.addWidget(w)
        side.addStretch()

        root = QWidget()
        layout = QHBoxLayout(root)
        layout.addWidget(self.canvas, 4)
        layout.addLayout(side, 1)
        self.setCentralWidget(root)

    # ---------- Load ----------
    def open_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Images Folder")
        if not folder:
            return
        self.images = [os.path.join(folder, f) for f in os.listdir(folder)
                       if f.lower().endswith((".jpg", ".png", ".jpeg"))]
        if not self.images:
            QMessageBox.warning(self, "Error", "No images found")
            return
        self.index = 0
        self.load_image()

    def load_image(self):
        self.scene.clear()
        self.crop_rects.clear()
        path = self.images[self.index]
        self.base_image = Image.open(path).convert("RGBA")
        self.scene.addPixmap(QPixmap(path))
        self.canvas.fitInView(self.scene.itemsBoundingRect(), Qt.KeepAspectRatio)

    # ---------- Processing ----------
    def normalize(self, w, h):
        return w - (w % 2), h - (h % 2)

    def process_images(self):
        if not self.crop_rects:
            QMessageBox.warning(self, "Error", "No crop zones")
            return

        out_root = "output"
        os.makedirs(out_root, exist_ok=True)
        name = os.path.splitext(os.path.basename(self.images[self.index]))[0]
        out_dir = os.path.join(out_root, name)
        os.makedirs(out_dir, exist_ok=True)

        for i, r in enumerate(self.crop_rects, 1):
            b = r.sceneBoundingRect()
            crop = self.base_image.crop((
                int(b.left()), int(b.top()),
                int(b.right()), int(b.bottom())
            ))

            # Circle mask
            if self.circle_mode.isChecked():
                mask = Image.new("L", crop.size, 0)
                draw = ImageDraw.Draw(mask)
                draw.ellipse((0, 0, crop.size[0], crop.size[1]), fill=255)
                crop.putalpha(mask)

            # Resize
            if self.resize_check.isChecked():
                w, h = self.normalize(self.w_edit.value(), self.h_edit.value())
                crop = crop.resize((w, h), Image.LANCZOS)

            # Enhance
            if self.enhance_check.isChecked():
                crop = enhance_image_opencv(crop.convert("RGB"))

            crop.save(os.path.join(out_dir, f"{i}.png"), format="PNG")

        QMessageBox.information(self, "Done", f"Saved to {out_dir}")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())
