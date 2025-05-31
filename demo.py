from PyQt5.QtWidgets import QWidget
from yuqtDraw.YmlAPIS.python import YAPP, APIEngine
from requests import get

class APP(YAPP):
    """
    必须继承自YAPP
    """

    def __init__(self, window, raw):
        self.window: QWidget = window
        self.api = APIEngine(raw)

    def TestButtonClicked(self, _btn):
        # 实际上你也可以_btn.setText(get("https://www.baidu.com").text)
        # 或者self.api.globals.globals("r", get("https://www.baidu.com").text)
        return {"r": get("https://www.baidu.com").text}  # 但是还是推荐使用return
