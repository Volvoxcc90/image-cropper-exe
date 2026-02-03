import sys, json, subprocess
from PySide6.QtWidgets import QApplication

def restart():
    subprocess.Popen([sys.executable] + sys.argv)
    sys.exit(0)

with open("settings.json") as f:
    ui = json.load(f)["ui_style"]

if ui == "fluent":
    from ui.fluent import MainWindow
elif ui == "material":
    from ui.material import MainWindow
elif ui == "minimal":
    from ui.minimal import MainWindow
elif ui == "studio":
    from ui.studio import MainWindow
else:
    from ui.saas import MainWindow

app = QApplication(sys.argv)
w = MainWindow(restart)
w.show()
sys.exit(app.exec())
