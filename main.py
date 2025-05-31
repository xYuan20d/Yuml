from PyQt5.QtWidgets import QApplication
from os import environ
environ["__YuQt_WindowStyle"] = "YW_root"
from yuqtDraw.Yuml import LoadYmlFile

app = QApplication([])
LoadYmlFile("test.yaml", app)
