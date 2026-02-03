import sys, json, os
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QFileDialog,
    QGraphicsView, QGraphicsScene, QPushButton
)
from PySide6.QtGui import QPixmap
from PySide6.QtCore import QRectF

class Cropper(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Image Cropper")
        self.resize(1200, 800)

        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene, self)
        self.setCentralWidget(self.view)

        self.rects = []

        btn = QPushButton("Открыть изображение", self)
        btn.move(10, 10)
        btn.clicked.connect(self.load_image)

        save = QPushButton("Сохранить шаблон", self)
        save.move(180, 10)
        save.clicked.connect(self.save_template)

    def load_image(self):
        file, _ = QFileDialog.getOpenFileName(self, "Image", "", "Images (*.png *.jpg)")
        if not file:
            return

        self.scene.clear()
        self.rects.clear()

        pix = QPixmap(file)
        self.scene.addPixmap(pix)

        for i in range(6):
            r = self.scene.addRect(QRectF(50+i*60, 80+i*40, 300, 200))
            r.setFlag(r.ItemIsMovable, True)
            r.setFlag(r.ItemIsSelectable, True)
            self.rects.append(r)

    def save_template(self):
        os.makedirs("templates", exist_ok=True)
        crops = []
        for r in self.rects:
            b = r.sceneBoundingRect()
            crops.append([int(b.left()), int(b.top()), int(b.right()), int(b.bottom())])

        with open("templates/custom_template.json", "w") as f:
            json.dump({"crops": crops}, f, indent=2)

        print("Шаблон сохранён")

app = QApplication(sys.argv)
w = Cropper()
w.show()
sys.exit(app.exec())
