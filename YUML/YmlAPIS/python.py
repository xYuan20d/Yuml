class YAPP:
    """
    一个脚本中只能拥有一个类作为YAPP的子类
    出现多个会执行最先定义的
    """
    pass


class APIEngine:

    def __init__(self, raw):
        from YUML.Yuml import LoadYmlFile, APIS  # 注意: import在开头会产生循环导入
        raw: tuple[LoadYmlFile, ...]
        self.self = raw[0]
        self.app: APIS.APP = raw[2]
