class YAPP:
    """
    一个脚本中只能拥有一个类作为YAPP的子类
    出现多个会执行最先定义的
    """
    pass


class APIEngine:

    def __init__(self, raw):
        self.globals = raw.API_G
