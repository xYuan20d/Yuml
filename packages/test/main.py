from PyQt5.QtWidgets import QComboBox, QPushButton
from YuanAPI.YNameSpace import YWidget, YWidgetBlock, YAddWidgetAttribute
from YuanAPI.YAPIS import YAPIEngine
from YuanAPI import YNameSpace

Y_NAMESPACE = YNameSpace

class comboBox(YWidget):
    def __init__(self, raw):
        super().__init__(raw, QComboBox)
        self.api = YAPIEngine(raw)
        self.clicked = self.api.onClicked
        self.string = self.api.string
        self.widget: QComboBox

    def widgetAttribute(self, key, value):
        if key == "items":
            for i in value:
                self.widget.addItem(self.string(i))

        elif key == "onClicked":
            func = lambda index, bid=self.string(value), _self=self.widget: self.clicked(bid, _self, index)
            self.widget.currentIndexChanged.connect(func)

        else:
            return False
