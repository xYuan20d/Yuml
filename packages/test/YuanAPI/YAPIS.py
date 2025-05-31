from ._apis import Globals, Default


class YAPIEngine:
    def __init__(self, raw):
        self.string: Default.string = raw.string
        self.onClicked: Default.onClicked = raw.clicked
        # ---
        self.globals: Globals = raw.API_G
