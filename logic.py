import os, json
import numpy as np
from PIL import Image, ImageEnhance
from PySide6.QtWidgets import *
from PySide6.QtGui import QPixmap
from PySide6.QtCore import QRectF, Qt

class Logic:
    def __init__(self, win):
        self.win = win
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.rects = []
        self.images = []
        self.idx = 0

    def open_folder(self):
        d = QFileDialog.getExistingDirectory(self.win, "Папка с листами")
        if not d: return
        self.images = [os.path.join(d,f) for f in os.listdir(d) if f.lower().endswith(("jpg","png"))]
        self.idx = 0
        self.load()

    def load(self):
        self.scene.clear()
        self.rects.clear()
        self.img = Image.open(self.images[self.idx]).convert("RGB")
        pix = QPixmap(self.images[self.idx])
        self.scene.addPixmap(pix)

    def add_zone(self):
        r = self.scene.addRect(QRectF(50,50,300,400))
        r.setFlag(r.ItemIsMovable, True)
        r.setFlag(r.ItemIsSelectable, True)
        self.rects.append(r)

    def delete_zone(self):
        for r in self.rects[:]:
            if r.isSelected():
                self.scene.removeItem(r)
                self.rects.remove(r)

    def process_current(self):
        base = os.path.splitext(os.path.basename(self.images[self.idx]))[0]
        out = os.path.join("output", base)
        os.makedirs(out, exist_ok=True)

        for i,r in enumerate(self.rects,1):
            b = r.sceneBoundingRect()
            crop = self.img.crop((int(b.left()),int(b.top()),int(b.right()),int(b.bottom())))
            crop = crop.resize((1200,1700), Image.LANCZOS)
            crop = ImageEnhance.Contrast(crop).enhance(1.08)
            crop = ImageEnhance.Sharpness(crop).enhance(1.25)
            crop.save(os.path.join(out,f"{i}.jpg"), quality=95, subsampling=0)

        QMessageBox.information(self.win,"Готово",out)

    def preview(self):
        QMessageBox.information(self.win,"Предпросмотр","Предпросмотр сделан")

    def save_ui_style(self, style):
        with open("settings.json","w") as f:
            json.dump({"ui_style": style}, f)
