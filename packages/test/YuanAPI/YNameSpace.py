from typing import Literal, Any, Dict, Callable
from abc import ABC, abstractmethod


class YLoad:
    def __init__(self, raw):
        self.raw = raw

class YMainBlock:
    def __init__(self, data, raw):
        self.data = data
        self.raw = raw

class YAddWidgetAttribute(ABC):
    def __init__(self, raw, widget):
        self.limit: tuple[str] = tuple()
        self.raw = raw
        self.widget = widget

    @abstractmethod
    def realize(self, value: Any) -> Dict[str, Callable[..., None]]:
        """
        该方法只需要返回值
        返回字典，键为str，值为可调用对象
        类名为add的组件名称，使用_YuGM_ + limit实现通配 + 过滤

        示例:
            return {"test": lambda: print(f"hello {value}")}
            给指定组件扩展了test方法，调用它会输出hello <值>
        """
        ...

class YWidgetBlock:
    def attribute(self, raw, value, widget) -> Literal[False] | None:
        return False

class YWidget:
    def __init__(self, window, widget):
        self.widget = widget(window)

    def widgetAttribute(self, key: str, value: Any) -> Literal[False] | None:
        """
        设置组件参数(重写类)
        没有指定参数返回False

        示例:
            if key == "hide":
                self.widget.hide() if value is True else self.widget.show()
            else:
                return False

        :param key: 键名
        :param value: 值
        :return: False或不返回
        """
        return False
