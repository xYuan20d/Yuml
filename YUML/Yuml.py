# coding: utf-8
from time import perf_counter
start_time = perf_counter()
from platform import system
system = system()
if system == "Windows":
    from winreg import OpenKey, HKEY_CURRENT_USER, QueryValueEx
elif system == "Darwin":
    from subprocess import run as runcommand
# ----
from re import sub
from json5 import load
from warnings import warn
from copy import deepcopy
from IPython import embed
from yaml import safe_load
from lupa import LuaRuntime
from jinja2 import Template
from threading import Thread
from datetime import datetime
from typing import Any as All
from importlib import import_module
from PyQt5.QtGui import QFont, QIcon
from os.path import dirname, abspath
from YUML.YmlAPIS.python import YAPP
from sys import stderr, path as spath
from inspect import isclass, getmembers
from YUML.script.YuanGuiScript import Script  # 自定义语言
from PyQt5.QtCore import QTimer, QObject, QEvent
from os import chdir, environ, path, listdir, getpid
from qframelesswindow import AcrylicWindow, FramelessWindow
from importlib.util import spec_from_file_location, module_from_spec
from colorama import Fore as Colors, Style, Back, init as color_init
from qframelesswindow.titlebar import MinimizeButton, CloseButton, MaximizeButton
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QListWidget, QMainWindow, QLineEdit


class QMW(QMainWindow):
    class TitleBar:
        @staticmethod
        def raise_():  pass

    def __init__(self, _p=None):
        super().__init__(_p)
        self.titleBar = self.TitleBar


# -- windowStyle (用户可通过环境变量设置) --
YW_ordinary = FramelessWindow
YW_acrylic = AcrylicWindow
YW_root = QMW

windowStyle = environ.get("__YuQt_WindowStyle", "YW_ordinary")
windowStyle = globals()[windowStyle]


def signalCall(func: All, func2):
    func.connect(func2)


class Warns:
    class YuanDeprecatedWarn(Warning):
        def __init__(self, *args): super().__init__(*args)


class Warps:
    @staticmethod
    def debug(conditions):
        def decorator(func):
            def warp(*args, **kwargs):
                if conditions == "CL":
                    if ("?" in args[1]) or __debug__:
                        return func(*args, **kwargs)

                    return None
                if __debug__ and (not conditions):  # 未使用 -O选项
                    return func(*args, **kwargs)

                return None
            return warp
        return decorator


class MoveEventFilter(QObject):
    def __init__(self, _widget, window, data):
        super().__init__(_widget)
        self.window = window
        self.data = data

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Move:
            self.window.call_block(self.window.string(self.data))
        return False  # 保留原行为


class Lua:
    class Any:
        def __setattr__(self, name, value):
            super().__setattr__(name, value)

        def __getattr__(self, name):
            return None

    def __init__(self, _self: "LoadYmlFile"):
        self.lua: LuaRuntime = ...
        self.self = _self

    def load(self):
        self.lua = LuaRuntime()
        self.lua.globals()._PY = __builtins__
        self.lua.globals().block = self.self.block
        self.lua.globals().window = self.self
        self.lua.globals().QTimer = QTimer
        self.lua.globals().signalCall = signalCall
        self.lua.globals().app = self.self.API_APP
        self.lua.globals()._G = self.self.API_G

    def execute(self, *args):
        if self.lua is not Ellipsis:
            self.lua.execute(*args)

    def globals(self):

        if self.lua is not Ellipsis:
            return self.lua.globals()

        return self.Any()


class APIS:
    class APP:
        class Python:
            def __init__(self, _window: "LoadYmlFile"):
                self.window = _window

            def call(self, name: str, *args, **kwargs) -> All:
                return getattr(self.window.python, name)(*args, **kwargs)

        class Console:
            class Q:
                def __init__(self, window):
                    self.window = window

                def __invert__(self):
                    self.window.app.quit()


        def __init__(self, app: QApplication, _window: "LoadYmlFile"):
            self.app: QApplication = app
            self.window = _window
            self.notExecErrors = []
            self._i18n = ("lang", "zh_cn.json5", "default.json5")
            self._i18n_data: dict | None = None
            self._i18n_def_data = None
            self.python = self.Python(_window)
            self._is_debug_start = False
            self._ListenSystemColorTimerModeTimer = None

        def run(self):
            self.app.exec_()

        def createWindow(self):
            self.window.show()

        def setFont(self, name, size):
            self.app.setFont(QFont(name, size))

        def notExecError(self, error: str):
            self.notExecErrors.append(error)

        def setPython(self, file: str):
            module = import_module(file)
            for name, obj in getmembers(module, isclass):
                if issubclass(obj, YAPP):
                    obj: All
                    self.window.python = obj(super(LoadYmlFile, self.window), (self.window, APIS, self.window.API_APP))
                    break

        def setTag(self, tag_name: str, *args):
            self.window.data = {}

            for i in self.window.findChildren(QWidget):
                if i not in [self.window.titleBar]:
                    # MaximizeButton CloseButton MinimizeButton
                    if type(i) not in [MaximizeButton, CloseButton, MinimizeButton]:
                        i.deleteLater() if i not in args else None

            with open(tag_name, "r", encoding="UTF-8") as file:
                chdir(dirname(abspath(tag_name)))
                self.window.data = safe_load(file)

            self.window.call_block("tagCalled")

        def setImportSelfPackageFolder(self, folder: str):
            """
            Yuml核心功能之一
            设置Yuml包导入文件夹 (自动遍历目录里面的包)
            :param folder: 目录
            """

            for i in listdir(folder):
                if i[0] == ".":
                    self.window.debug_print(f"忽略包: {i}")
                    continue
                spath.append(path.join(folder, i))
                module = self.window.load_module("main", path.join(folder, i, "main.py"))

                base_classes = {
                    module.Y_NAMESPACE.YMainBlock: lambda _obj: self.window.main_block_module.append(_obj),
                    module.Y_NAMESPACE.YWidget: lambda _obj: self.window.widget_block_module.append(_obj),
                    module.Y_NAMESPACE.YLoad: lambda _obj: _obj(self.window),
                    module.Y_NAMESPACE.YWidgetBlock: lambda _obj: self.window.widgetBlock_block_module.append(_obj),
                    module.Y_NAMESPACE.YAddWidgetAttribute: lambda _obj: self.window.widget_add_block_module.append(_obj)
                }

                for name, obj in getmembers(module, isclass):
                    for base, handler in base_classes.items():
                        if issubclass(obj, base) and obj != base:
                            handler(obj)

        def importPackage(self, *args):
            """
            简单导入 (通过importlib.import_module)
            写上导入的模块名字(字符串)即可
            """
            for i in args:
                split = i.split(" ")
                name = split[1] if len(split) != 1 else split[0]

                module = import_module(split[0])

                self.window.API_G.globals(name, module)

        def comImportPackage(self, python_code: str, module_name: str):
            """
            复杂导入
            示例: comImportPackage("from math import sqrt, pi", "sqrt pi")

            :param python_code: 通过exec执行python导入代码
            :param module_name: 导入的模块，空格隔开
            """
            exec(python_code)
            for i in module_name.split(" "):
                try:
                    self.window.API_G.globals(i, globals()[i])
                except KeyError:
                    raise NameError(f"`{i}`未找到")

        def setI18n(self, folder, file, default_file):
            """
            配置i18n (internationalization)

            :param folder: 翻译文件夹
            :param file: 默认当前文件
            :param default_file: 默认文件
            """
            self._i18n = (folder, file, default_file)

        def i18n(self, name):
            if self._i18n_data is None:
                with open(path.join(self._i18n[0], self._i18n[1]), "r", encoding="UTF-8") as f:
                    self._i18n_data = load(f)
            if self._i18n_def_data is None:
                with open(path.join(self._i18n[0], self._i18n[2]), "r", encoding="UTF-8") as f:
                    self._i18n_def_data = load(f)

            try:
                return self._i18n_data[name]
            except KeyError:
                if self._i18n_def_data.get(name) is None:
                    raise NameError(f"{name} 未找到")
                return self._i18n_def_data[name]

        @Warps.debug("CL")
        def setConsoleLog(self, mode: str):
            """
            调试器
            当python解释器使用-O选项时, 该函数不会执行(除使用?操作符)
            不建议在生产时开启
            """
            from psutil import Process
            rss_peak = 0
            vms_peak = 0
            pid = getpid()
            def Perf():
                nonlocal rss_peak, vms_peak
                p = Process(pid)
                rams = p.memory_info()
                rss = rams.rss // 1024
                vms = rams.vms // 1024
                if rss > rss_peak:
                    rss_peak = rss
                if vms > vms_peak:
                    vms_peak = vms

                print(f"\r{Back.RED}{Style.BRIGHT}[性能监控] [PID: {pid}] [内存(KB) | RSS: {rss} (峰值: {rss_peak}), "
                      f"VMS: {vms} (峰值: {vms_peak})]{Style.RESET_ALL}", end="", flush=True)

            def getPerf():
                while True:
                    Perf()

            q = self.Console.Q(self.window)
            if not self._is_debug_start:
                color_init()
                print(f"{Back.WHITE}{Style.BRIGHT}{Colors.MAGENTA}"
                      f"Yuml Loader (c) YY | Version: {self.window.version}\n"
                      f"<YML Debug Tool> - <v0.0.1beta> (仅用于调试目的, 请在生产环境关闭)\n"
                      f"{self.window.Symbols.SEPARATION}\n{Style.RESET_ALL}")
                self._is_debug_start = True

            for i in mode.replace(" ", ""):
                if i == "D":
                    # 启动Debug模式
                    self.window.debug_print = \
                        lambda v: print(f"{Colors.YELLOW}[DEBUG] | {datetime.now()}: {v}{Style.RESET_ALL}")

                elif i == "I":
                    # 启动Info模式
                    self.window.info_print = \
                        lambda v: print(f"{Colors.GREEN}[INFO] | {datetime.now()}: {v}{Style.RESET_ALL}")

                elif i == "/":
                    # 移除Debug模式
                    self.window.debug_print = self.window.NN

                elif i == ".":
                    # 移除Info模式
                    self.window.info_print = self.window.NN

                elif i == "C":
                    # 启动Console
                    Thread(target=embed, daemon=True,
                           kwargs={"header": f"{Back.GREEN}{Colors.BLACK}Yuml Loader Tool Console{Style.RESET_ALL}",
                           "user_ns": locals()}).start()

                elif i == "R":
                    # 启动性能检测(启用后其他模式不生效)
                    Thread(target=getPerf, daemon=True).start()

        def setDarkMode(self):
            """
            openListenSystemColorMode的切换颜色功能
            你可以手动调用他进行切换
            """
            if self.window.data.get("darkMode") is not None:
                self.window.call_block("darkMode")

            for i in self.window.findChildren(QWidget):
                i.darkQssStyle(i) if hasattr(i, "darkQssStyle") and callable(getattr(i, 'darkQssStyle')) else None

        def setLightMode(self):
            """
            同上 (setDarkMode)
            :return:
            """
            if self.window.data.get("lightMode") is not None:
                self.window.call_block("lightMode")

            for i in self.window.findChildren(QWidget):
                i.lightQssStyle(i) if hasattr(i, "lightQssStyle") and callable(getattr(i, 'lightQssStyle')) else None


        def openListenSystemColorMode(self):
            """
            开启监控系统颜色模式功能
            """
            if self._ListenSystemColorTimerModeTimer is not None:
                return

            current = None
            def update():
                nonlocal current

                if self.window.is_dark_mode():  # 深色
                    if current is not True:
                        current = True
                        self.setDarkMode()

                else:
                    if current is not False:
                        current = False
                        self.setLightMode()

            self._ListenSystemColorTimerModeTimer = QTimer(self.window)
            signalCall(self._ListenSystemColorTimerModeTimer.timeout, update)
            self._ListenSystemColorTimerModeTimer.start(1)

        def closeListenSystemColorMode(self):
            """
            关闭监控系统颜色模式功能
            """
            if self._ListenSystemColorTimerModeTimer is not None:
                self._ListenSystemColorTimerModeTimer.stop()
                self._ListenSystemColorTimerModeTimer = None


    class Console:
        """
        针对YuanGuiScript的输出功能
        """
        @staticmethod
        def log(v):
            print(v)


    class Widget:
        def __init__(self, _widget: QWidget):
            self.widget = _widget

        def show(self):
            self.widget.show()

        def hide(self):
            self.widget.hide()

        def move(self, x, y):
            self.widget.move(x, y)

        def resize(self, w, h):
            self.widget.resize(w, h)

        def raw(self, name, *args):
            return getattr(self.widget, name)(*args)


    class Lua:
        def __init__(self, lua):
            self.lua = lua

        def run(self):
            self.lua.load()


    class Block:
        def __init__(self, _exec: "LoadYmlFile"):
            self.notExecBlock = []
            self._exec = _exec

        def notExec(self, block: str):
            """
            不执行特定块的代码
            :param block: 块名
            """
            self.notExecBlock.append(block)

        def execBlockCode(self, block_code: str, scope: str | list):
            """
            执行string块
            因技术问题，该方法暂时无法实现
            """
            ...


    class G:
        def __init__(self, _lua: Lua, _script_g: dict, _eval: dict):
            self.lua = _lua
            self.G = _script_g
            self.eval = _eval

        def globals(self, name: All, value: All):
            """
            创建全局命名空间
            :param name: 名称
            :param value: 值
            """
            self.eval[name] = value
            setattr(self.lua.globals(), name, value)
            self.G[name] = value

        def getGlobals(self, name: All, default=None) -> All:
            """
            用于验证目的
            正常创建全局命名可以使用
            :param name: 名称
            :param default: 未找到时返回
            """
            return self.eval.get(name, default)

        def delGlobals(self, name: All):
            """
            删除全局命名空间
            :param name: 名称
            """
            del self.eval[name]
            setattr(self.lua.globals(), name, None)
            del self.G[name]


class LoadYmlFile(FramelessWindow):  # dev继承自FramelessWindow / build时将它改为继承windowStyle

    class RWidgets:
        def __init__(self, cw: "LoadYmlFile.create_widget"):
            self.createWidget = cw

        def button(self, data, scope):
            self.createWidget("button", data, scope)

        def label(self, data, scope):
            self.createWidget("label", data, scope)

        def listBox(self, data, scope):
            self.createWidget("listBox", data, scope)

        def input(self, data, scope):
            self.createWidget("input", data, scope)

        def yumlWidget(self, data, scope):
            self.createWidget("YUML_WIDGET", data, scope)

        def dynamic(self, data, scope, obj):
            self.createWidget(obj, data, scope)

    class Symbols:
        ASSIGNMENT = "=>"
        RAW = "->>"
        SEPARATION = "--------------------"


    def __init__(self, file_name: str, app: QApplication, load_str: bool = False,
                 is_module: bool = False, _p=None):
        self.time = perf_counter()
        super().__init__(_p)
        self.version = (0, 0, 0, 1, "beta")
        self.python = None
        self.NN = lambda x: None
        self.main_block_module = []
        self.widget_block_module = []
        self.widget_add_block_module = []
        self.widgetBlock_block_module = []
        self.execResizeEvent = False
        self.lua = Lua(self)
        self.app = app
        self.titleBar.raise_()
        self._is_create = False
        self.debug_print = self.NN
        self.info_print = self.NN
        self.block = APIS.Block(self)
        self.API_APP = APIS.APP(self.app, self)
        self._G: dict = {"app": self.API_APP, "Console": APIS.Console(), "Lua": APIS.Lua(self.lua), "block":
                        self.block, "window": super()}
        self.eval_globals = {
            "math": __import__("math"),
            "window": super(),
            "app": self.API_APP
        }
        self.global_args = [self.lua, self._G, self.eval_globals]
        self.API_G = APIS.G(*self.global_args)
        self._G["_G"] = self.API_G
        self.cw = self.RWidgets(self.create_widget)
        if load_str:
            chdir(dirname(abspath(__file__)))
            self.data: dict = safe_load(Template(file_name).render())
        else:
            with open(file_name, "r", encoding="UTF-8") as file:
                chdir(dirname(abspath(file_name)))
                self.data: dict = safe_load(Template(file.read()).render())

        if "template" in self.data:
            warn("template在新版本中被移除, 使用yaml锚点实现相同功能", category=Warns.YuanDeprecatedWarn)

        self.definedQss()
        if not is_module:
            for i in self.data["run"]:
                self.main_block(i, "run")
        else:
            for i in self.data["widget"]:
                self.main_block(i, "widget")

    @staticmethod
    def load_module(module_name, file_path):
        spec = spec_from_file_location(module_name, file_path)
        module = module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def error_print(self, msg: All, _id):
        if _id not in self.API_APP.notExecErrors:
            print(f"错误: {msg} ({_id})", file=stderr)

    def is_dark_mode(self):
        if system == "Darwin":
            try:
                result = runcommand(
                    ['defaults', 'read', '-g', 'AppleInterfaceStyle'],
                    capture_output=True,
                    text=True
                )
                return result.stdout.strip() == 'Dark'
            except Exception as e:
                self.error_print(e, "colorModeError")
                return False
        elif system == "Windows":
            try:
                key = OpenKey(HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
                return QueryValueEx(key, "AppsUseLightTheme")[0] == 0  # 深色
            except Exception as e:
                self.error_print(f"获取注册表出现了未知错误 {e}", "KeyError")
                return False
        else:
            self.error_print(f"{system}不受深色模式支持", "colorModeSystemError")
            return False

    def call_block(self, scope, accept=None):
        for i in self.data[scope]:
            if scope in self.block.notExecBlock:
                self.block.notExecBlock.remove(scope)
                return

            self.main_block(i, scope, accept)

    def widget(self, key: str, data, widget: QWidget, scope: list | str, name: str):
        match key:
            case "show":  widget.setVisible(self.string(data[key]))

            case "move":  widget.move(self.string(data[key]["x"]), self.string(data[key]["y"]))

            case "size":  widget.resize(self.string(data[key]["width"]), self.string(data[key]["height"]))

            case "X":  widget.move(self.string(data[key]), widget.y())

            case "Y":  widget.move(widget.x(), self.string(data[key]))

            case "width":  widget.resize(self.string(data[key]), widget.height())

            case "height":  widget.resize(widget.width(), self.string(data[key]))

            case "QssStyle":  widget.setStyleSheet(self.string(data[key]))

            case "id":  widget.setObjectName(self.string(data[key]))

            case "onMoved":

                widget.installEventFilter(MoveEventFilter(widget, self, data[key]))

            case "darkStyle":
                setattr(widget, "darkQssStyle", lambda _self, style=self.string(data[key]): _self.setStyleSheet(style))

            case "lightStyle":
                setattr(widget, "lightQssStyle", lambda _self, style=self.string(data[key]): _self.setStyleSheet(style))

            case _:
                def load_package():
                    _is = None
                    for _i in self.widgetBlock_block_module:
                        if _i.__name__ == key:
                            if _i().attribute({"LoadYmlFile": self}, data[key], widget) is False:
                                return None
                            _is = True
                            self.debug_print(f"加载Package Widget Block({key} {self.Symbols.RAW} ({_i})")

                    return _is

                if load_package() is None:
                    _scope = deepcopy(scope)
                    _scope.append(name)
                    self.main_block(key, _scope)

    def create_widget(self, widget_type, data, scope):
        widget_creators = {
            "button": lambda: QPushButton(self),
            "label": lambda: QLabel(self),
            "listBox": lambda: QListWidget(self),
            "input": lambda: QLineEdit(self),
        }

        widget_limit = {
            "text": ["button", "label", "input"],
            "enabled": ["button", "input"],
            "onClicked": ["button"],
            "items": ["listBox"],
            "itemOnClicked": ["listBox"],
            "itemDrag": ["listBox"],
            "textChanged": ["input"],
            "returnPressed": ["input"],
            "passwordMode": ["input"],
            "placeholderText": ["input"]
        }

        attribute_handlers = {
            "text": lambda w, v: w.setText(self.string(v)),
            "enabled": lambda w, v: w.setEnabled(v),
            "onClicked": lambda w, v: signalCall(w.clicked, lambda _, bid=self.string(v), _w=w: self.clicked(bid, _w)),
            "items": lambda w, v: [w.addItem(self.string(i)) for i in v],
            "itemOnClicked": lambda w, v: signalCall(w.itemClicked,
                                                     lambda text, bid=self.string(v), _w=w: self.clicked(bid, _w,
                                                                                                         text)),
            "itemDrag": lambda w, v: w.setDragDropMode(QListWidget.InternalMove if v else QListWidget.NoDragDrop),
            "textChanged": lambda w, v: signalCall(w.textChanged,
                                                   lambda text, bid=self.string(v), _w=w: self.clicked(bid, _w, text)),
            "placeholderText": lambda w, v: w.setPlaceholderText(self.string(v)),
            "returnPressed": lambda w, v: signalCall(w.returnPressed,
                                                     lambda bid=self.string(v), _w=w: self.clicked(bid, _w, _w.text())),
            "passwordMode": lambda w, v: w.setEchoMode(QLineEdit.Password) if v else None,
        }

        for _i in data:
            _widget = None
            if widget_type == "YUML_WIDGET":
                widget = LoadYmlFile(data[_i]["type"], self.app, _p=self, is_module=True)
                del data[_i]["type"]
            else:
                widget = widget_creators.get(widget_type, lambda: None)()
            if not widget:
                _widget = widget_type(self)
                widget_type = widget_type.__name__
                widget = _widget.widget

            self.API_G.globals(_i, widget)
            for key, val in data[_i].items():
                limit = widget_limit.get(key, [])
                if key in attribute_handlers and widget_type in limit:
                    attribute_handlers[key](widget, val)
                    continue

                is_rep = False
                for mod in self.widget_add_block_module:
                    if mod.__name__ in (widget_type, "_YuGM_"):
                        mod_instance = mod(self, widget_type, widget)
                        if (widget_type not in mod_instance.limit) and mod_instance.limit:
                            continue
                        try:
                            datas = mod_instance.realize(val)
                            if datas.get(key):
                                datas[key]()
                                is_rep = True
                        except AttributeError:
                            continue

                if is_rep:
                    continue

                if getattr(_widget, "widgetAttribute", None):
                    if _widget.widgetAttribute(key, self.string(val)) is not False:
                        continue

                _scope = [scope, widget_type] if isinstance(scope, str) else deepcopy(scope).append(widget_type)
                self.widget(key, data[_i], widget, _scope, _i)

    def main_block(self, block_name: str, scope: str | list, _accept=None):
        blocks = block_name.split("_")
        _block_name = blocks[0]
        if len(blocks) > 2:
            self.debug_print(f"{block_name} `_` 数量超过1(自动跳过)")
            _block_name = block_name

        try:
            int(blocks[1])
        except ValueError:
            self.debug_print(f"{block_name} `_` 后不是数字(自动跳过)")
            _block_name = block_name
        except IndexError:
            pass

        if isinstance(scope, list):
            data = self.data
            for i in scope:
                data = data[i]

            data = data[block_name]
        else:
            data = self.data[scope][block_name]

        self.debug_print(f"{block_name} 去除`_`: {_block_name} ({scope})")

        match _block_name:
            case "windowSize":
                self.resize(self.string(data["width"]), self.string(data["height"]))
            case "windowTitle":
                self.setWindowTitle(self.string(data))
            case "windowIcon":
                self.setWindowIcon(QIcon(self.string(data)))
            case "globalStyle":
                self.setStyleSheet(self.string(data))
            case "button":
                self.cw.button(data, scope)
            case "label":
                self.cw.label(data, scope)
            case "listBox":
                self.cw.listBox(data, scope)
            case "input":
                self.cw.input(data, scope)
            case "YUML_WIDGET":
                self.cw.yumlWidget(data, scope)
            case "YuanGuiScript":
                Script(data, self._G)
            case "LuaScript":
                self.lua.execute(data)
            case "QssStyle":
                self.setStyleSheet(self.string(data))
            case "PythonScript":
                exec(data, self.eval_globals)

            case _:
                raw = block_name
                self.debug_print(f"未找到默认block, 已将block替换为原名({_block_name} {self.Symbols.ASSIGNMENT} {raw})")

                def load_package():
                    for modules, handler in [
                        (self.main_block_module, lambda _mod: _mod(data, self)),
                        (self.widget_block_module, lambda _mod: self.cw.dynamic(data, scope, _mod)),
                    ]:
                        for mod in modules:
                            if mod.__name__ == raw:
                                handler(mod)
                                block_type = "Block" if modules is self.main_block_module else "Widget"
                                self.debug_print(f"加载Package {block_type}({raw} {self.Symbols.RAW} {mod})")
                                return True
                    return None


                if block_name[0] not in ["\\"]:
                    block_name = block_name.split("<")
                    if len(block_name) != 1:
                        for i in block_name[1:]:
                            if i == "notExec":
                                break

                            else:
                                self.error_print(f"`{i}`操作不存在", "NoCommandError")
                    else:
                        if load_package() is None:
                            self.error_print(f"没有名为`{block_name[0]}`的元素", "NoBlockError")

                else:
                    block_name = block_name[1:]
                    block = block_name[1:]
                    match block_name[0]:
                        case "=":
                            self.API_G.globals(block, self.string(data))
                        case ">":
                            if data == ".accept":
                                self.API_G.globals(block, _accept)
                            else: self.API_G.globals(block, eval(data, self.eval_globals))
                        case "#":
                            if (data == "python") or (data is None):
                                exec(block, self.eval_globals)
                            elif data == "lua":
                                self.lua.execute(block)
                            elif data == "YuanGuiScript":
                                Script(data, self._G)

        self.titleBar.raise_()

    def definedQss(self):
        data: dict = self.data.get("definedQss")
        if not data:
            return

        qss_list = []

        for k, v in data.items():
            k = sub(r'^\$', '#', k)
            declarations = '; '.join(f"{k}: {v}" for k, v in v.items())
            qss_list.append(f"{k} {{ {declarations}; }}")

        qss = '\n'.join(qss_list)
        self.app.setStyleSheet(self.app.styleSheet() + '\n' + qss)

    def showEvent(self, a0):
        super().showEvent(a0)
        if self._is_create:
            if self.data.get("windowShowed"):
                self.call_block("windowShowed")
            return

        self._is_create = True

        if self.data.get("windowCreated") is not None:
            self.call_block("windowCreated")

            current = perf_counter()
            self.info_print(f"启动用时: {current - self.time} {self.Symbols.RAW} "
                            f"({current - start_time})\n{self.Symbols.SEPARATION}\n")

    def moveEvent(self, a0):
        super().moveEvent(a0)
        try:
            if self.data.get("windowMoved") is not None:
                self.call_block("windowMoved")
        except AttributeError:
            pass

    def resizeEvent(self, a0):
        super().resizeEvent(a0)

        if not self.execResizeEvent:
            self.execResizeEvent = True  # PyQt第一次创建窗口时，会调用resizeEvent，屏蔽第一次创建窗口事件
            return

        if self.data.get("windowResized") is not None:
            self.call_block("windowResized")

    def hideEvent(self, a0):
        if self.data.get("windowHidden") is not None:
            self.call_block("windowHidden")

    def closeEvent(self, event):
        setattr(event, "Yes", event.accept)
        setattr(event, "No", event.ignore)
        if self.data.get("windowClosed") is not None:
            self.call_block("windowClosed", event)
        else:
            super().closeEvent(event)
            event.Yes()

    def clicked(self, wid: str, widget, text=None):
        if self.python is not None:
            try:
                if text is not None:
                    name = getattr(self.python, wid)(widget, text)
                else:
                    name = getattr(self.python, wid)(widget)
                if isinstance(name, dict):
                    for i in name:
                        self.API_G.globals(i, name[i])
            except AttributeError:
                pass

        if self.data.get(wid) is None:
            return

        self.call_block(wid, text)

    def string(self, s):
        """
        字符串渲染引擎
        """
        if not isinstance(s, str):
            return s

        is_rep = False
        eval_result = None

        def rep(m):
            nonlocal is_rep, eval_result
            try:
                is_rep = True
                eval_result = eval(m.group(1).strip(), self.eval_globals)
                return str(eval_result)
            except Exception as error:
                self.error_print(error, "StringError")
                return ""

        _str = sub(r'\{\{<<(.*?)>>}}', r'{<\1>}', sub(r'\{<\s*([^>]+?)\s*>}', rep, s)).strip()
        if not is_rep:
            return _str

        try:
            s = _str[:-5] + _str[-4:]
            if _str.endswith(":int"):
                # 从特定角度来说, :int可以被:obj方法代替(int(code) :obj), 但出于可读性考虑, 保留该功能
                return int(_str[:-4]) if _str[-5] != ":" else s

            elif _str.endswith(":obj"):
                return eval_result if _str[-5] != ":" else s
            else:
                return _str
        except IndexError:
            return _str


if __name__ == '__main__':
    print("请打开`demos`目录查看示例")
