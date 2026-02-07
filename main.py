# Full-featured Desktop Infographic Editor + Crop + OpenCV Enhancement
# REQUIREMENTS:
#   pip install PySide6 Pillow opencv-python numpy

import sys, os
import numpy as np
import cv2
from PIL import Image

# ---------- PySide6 safety import ----------
try:
    from PySide6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
        QPushButton, QListWidget, QListWidgetItem, QFileDialog,
        QColorDialog, QSlider, QLabel, QSpinBox, QMessageBox, QComboBox,
        QGraphicsView, QGraphicsScene, QGraphicsRectItem,
        QGraphicsTextItem, QGraphicsPixmapItem
    )
    from PySide6.QtGui import QPixmap, QColor, QFont, QImage, QPainter, QPen
    from PySide6.QtCore import Qt, QRectF
except ModuleNotFoundError:
    print("ERROR: PySide6 not installed. Run: pip install PySide6 Pillow opencv-python numpy")
    sys.exit(1)


# ================= OpenCV Image Enhancement =================
def enhance_image_opencv(pil_img, target_w, target_h):
    img = np.array(pil_img)
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

    # High quality resize
    img = cv2.resize(img, (target_w, target_h), interpolation=cv2.INTER_CUBIC)

    # Local sharpening (Unsharp Mask)
    blur = cv2.GaussianBlur(img, (0, 0), 1.2)
    sharp = cv2.addWeighted(img, 1.4, blur, -0.4, 0)

    # Local contrast via LAB + CLAHE
    lab = cv2.cvtColor(sharp, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l = clahe.apply(l)
    lab = cv2.merge((l, a, b))
    final = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)

    return Image.fromarray(final)


# ================= Graphics View with Crop Drawing =================
class Canvas(QGraphicsView):
    def __init__(self, scene, app):
        super().__init__(scene)
        self.app = app
        self.start_pos = None
        self.temp_rect = None
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)

    def wheelEvent(self, e):
        if e.modifiers() & Qt.ControlModifier:
            factor = 1.15 if e.angleDelta().y() > 0 else 0.87
            self.scale(factor, factor)
        else:
            super().wheelEvent(e)

    def mousePressEvent(self, e):
        if self.app.crop_mode and e.button() == Qt.LeftButton:
            self.start_pos = self.mapToScene(e.pos())
            self.temp_rect = QGraphicsRectItem(QRectF(self.start_pos, self.start_pos))
            self.temp_rect.setPen(QPen(QColor(0, 200, 255), 2))
            self.scene().addItem(self.temp_rect)
        else:
            super().mousePressEvent(e)

    def mouseMoveEvent(self, e):
        if self.temp_rect:
            rect = QRectF(self.start_pos, self.mapToScene(e.pos())).normalized()
            self.temp_rect.setRect(rect)
        else:
            super().mouseMoveEvent(e)

    def mouseReleaseEvent(self, e):
        if self.temp_rect:
            rect = self.temp_rect.rect()
            self.scene().removeItem(self.temp_rect)
            if rect.width() > 10 and rect.height() > 10:
                r = QGraphicsRectItem(rect)
                r.setPen(QPen(QColor(255, 180, 0), 2))
                r.setFlag(QGraphicsRectItem.ItemIsMovable, True)
                r.setFlag(QGraphicsRectItem.ItemIsSelectable, True)
                self.scene().addItem(r)
                self.app.crop_rects.append(r)
            self.temp_rect = None
        else:
            super().mouseReleaseEvent(e)


# ================= Main Application =================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Crop + Infographic Pro")
        self.resize(1500, 900)

        self.scene = QGraphicsScene()
        self.canvas = Canvas(self.scene, self)

        self.images = []
        self.index = 0
        self.base_image = None
        self.crop_rects = []
        self.crop_mode = False

        # UI controls
        self.layers = QListWidget()
        self.layers.currentRowChanged.connect(self.select_layer)

        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(0, 100)
        self.opacity_slider.valueChanged.connect(self.set_opacity)

        self.font_size = QSpinBox()
        self.font_size.setRange(8, 200)
        self.font_size.valueChanged.connect(self.set_font_size)

        self.font_family = QComboBox()
        self.font_family.addItems(["Arial", "Times New Roman", "Courier New", "Verdana"])
        self.font_family.currentTextChanged.connect(self.set_font_family)

        self.w_edit = QSpinBox(); self.w_edit.setRange(100, 4000); self.w_edit.setValue(1200)
        self.h_edit = QSpinBox(); self.h_edit.setRange(100, 4000); self.h_edit.setValue(1700)

        # Buttons
        btn_open = QPushButton("Open Folder")
        btn_open.clicked.connect(self.open_folder)

        btn_crop = QPushButton("Crop Mode")
        btn_crop.clicked.connect(lambda: setattr(self, 'crop_mode', not self.crop_mode))

        btn_text = QPushButton("Add Text")
        btn_text.clicked.connect(self.add_text)

        btn_rect = QPushButton("Add Shape")
        btn_rect.clicked.connect(self.add_shape)

        btn_image = QPushButton("Add PNG")
        btn_image.clicked.connect(self.add_image)

        btn_color = QPushButton("Color")
        btn_color.clicked.connect(self.set_color)

        btn_export = QPushButton("Process & Export")
        btn_export.clicked.connect(self.process_and_export)

        # Layouts
        side = QVBoxLayout()
        for w in [btn_open, btn_crop, QLabel("Resize"), self.w_edit, self.h_edit,
                  btn_text, btn_rect, btn_image, QLabel("Font"), self.font_family,
                  QLabel("Font Size"), self.font_size, QLabel("Opacity"), self.opacity_slider,
                  btn_color, btn_export]:
            side.addWidget(w)
        side.addStretch()

        root = QWidget()
        layout = QHBoxLayout(root)
        layout.addWidget(self.canvas, 4)
        layout.addLayout(side, 1)
        self.setCentralWidget(root)

    # ---------- Image loading ----------
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
        self.base_image = Image.open(path).convert("RGB")
        self.scene.addPixmap(QPixmap(path))
        self.canvas.fitInView(self.scene.itemsBoundingRect(), Qt.KeepAspectRatio)

    # ---------- Layers ----------
    def current_item(self):
        row = self.layers.currentRow()
        if row < 0:
            return None
        return self.layers.item(row).data(Qt.UserRole)

    def add_layer(self, name, item):
        li = QListWidgetItem(name)
        li.setData(Qt.UserRole, item)
        self.layers.addItem(li)
        self.layers.setCurrentItem(li)
        item.setFlag(item.ItemIsMovable, True)
        item.setFlag(item.ItemIsSelectable, True)

    def select_layer(self, _):
        item = self.current_item()
        if item:
            self.opacity_slider.setValue(int(item.opacity() * 100))

    # ---------- Add elements ----------
    def add_text(self):
        t = QGraphicsTextItem("TEXT")
        t.setFont(QFont("Arial", 40))
        t.setDefaultTextColor(QColor("white"))
        self.scene.addItem(t)
        self.add_layer("Text", t)

    def add_shape(self):
        r = QGraphicsRectItem(0, 0, 300, 120)
        r.setBrush(QColor(255, 255, 255, 180))
        self.scene.addItem(r)
        self.add_layer("Shape", r)

    def add_image(self):
        path, _ = QFileDialog.getOpenFileName(self, "PNG", "", "Images (*.png *.jpg)")
        if not path:
            return
        p = QGraphicsPixmapItem(QPixmap(path))
        self.scene.addItem(p)
        self.add_layer("Image", p)

    # ---------- Properties ----------
    def set_opacity(self, v):
        item = self.current_item()
        if item:
            item.setOpacity(v / 100)

    def set_font_size(self, v):
        item = self.current_item()
        if isinstance(item, QGraphicsTextItem):
            f = item.font(); f.setPointSize(v); item.setFont(f)

    def set_font_family(self, fam):
        item = self.current_item()
        if isinstance(item, QGraphicsTextItem):
            f = item.font(); f.setFamily(fam); item.setFont(f)

    def set_color(self):
        item = self.current_item()
        if not item:
            return
        c = QColorDialog.getColor()
        if not c.isValid():
            return
        if isinstance(item, QGraphicsTextItem):
            item.setDefaultTextColor(c)
        elif isinstance(item, QGraphicsRectItem):
            item.setBrush(c)

    # ---------- Final Processing ----------
    def process_and_export(self):
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
            crop = self.base_image.crop((int(b.left()), int(b.top()), int(b.right()), int(b.bottom())))
            result = enhance_image_opencv(crop, self.w_edit.value(), self.h_edit.value())
            result.save(os.path.join(out_dir, f"{i}.jpg"), quality=95, subsampling=0)

        QMessageBox.information(self, "Done", f"Saved to {out_dir}")


# ================= Entry =================
if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())
