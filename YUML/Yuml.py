# coding: utf-8
from time import perf_counter
start_time = perf_counter()
from platform import system
system = system()
if system == "Windows":
    from winreg import OpenKey, HKEY_CURRENT_USER, QueryValueEx
elif system == "Darwin":
    from subprocess import run as runcommand
from re import sub, finditer
from json5 import load
from warnings import warn
from copy import deepcopy
from IPython import embed
from lupa import LuaRuntime
from jinja2 import Template
from ruamel.yaml import YAML
from functools import reduce
from threading import Thread
from datetime import datetime
from typing import Any as All
from importlib import import_module
from os.path import dirname, abspath
from YUML.YmlAPIS.python import YAPP
from contextlib import contextmanager
from PySide6.QtGui import QFont, QIcon
from inspect import isclass, getmembers
from YUML.script.YuanGuiScript import Script  # 自定义语言
from collections import OrderedDict, defaultdict
from PySide6.QtCore import QTimer, QObject, QEvent
from os import chdir, environ, path, listdir, getpid
from YUML.data.YSQLite import is_sqlite_file, SQLiteDict
from qframelesswindow import AcrylicWindow, FramelessWindow
from sys import stderr, path as sys_path, modules as sys_modules
from importlib.util import spec_from_file_location, module_from_spec
from colorama import Fore as Colors, Style, Back, init as color_init
from qframelesswindow.titlebar import MinimizeButton, CloseButton, MaximizeButton
from PySide6.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QListWidget, QMainWindow, QLineEdit


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

APPLICATION = QApplication

def signalCall(func: All, func2):
    """
    调用qt signalCall所设计, 起初是为了支持Lua使用
    现Yuml已全面移植到PySide6, signalCall已弃用
    """
    func.connect(func2)


class Warns:
    class YuanDeprecatedWarn(Warning):
        def __init__(self, *args):
            super().__init__(*args)


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
    def __init__(self, _widget, window: "LoadYmlFile", data):
        super().__init__(_widget)
        self.widget = _widget
        self.window = window
        self.data = data

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.Move:
            if isinstance(obj, str):
                self.window.call_block(self.window.string(self.data), self.widget)
            else:
                self.window.exec_code(self.data)
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


        def __init__(self, app: APPLICATION, _window: "LoadYmlFile"):
            self.app: APPLICATION = app
            self.window = _window
            self.notExecErrors = []
            self._i18n = ("lang", "zh_cn.json5", "default.json5")
            self._i18n_data: dict | None = None
            self._i18n_def_data = None
            self.python = self.Python(_window)
            self.package_sequence = []
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
                    self.window.python = obj(self.window)
                    break

        def setTag(self, tag_name: str, *args):
            """
            Yuml核心概念之一
            分页开发, 就像html一样切换切换页(类似javascript的window.location.replace)

            :param tag_name: 文件名
            :param args: 排除项
            """
            self.window.data = {}

            for i in self.window.findChildren(QWidget):
                if i not in [self.window.titleBar]:
                    # MaximizeButton CloseButton MinimizeButton 排除这三个控制窗口的按钮
                    if type(i) not in [MaximizeButton, CloseButton, MinimizeButton]:
                        i.deleteLater() if i not in args else None

            self.window.yaml.load_file(tag_name)

            self.window.call_block("tagCalled")

        @staticmethod
        @contextmanager
        def _temp_sys_path(_path):
            """
            临时将包路径加入 sys.path，退出时移除
            """
            sys_path.insert(0, _path)
            try:
                yield
            finally:
                if _path in sys_path:
                    sys_path.remove(_path)

        @staticmethod
        def _safe_load_module(unique_module_name: str, file_path: str) -> All:
            """
            沙箱隔离环境加载包
            """
            old_modules = sys_modules.copy()
            try:
                spec = spec_from_file_location(unique_module_name, file_path)
                module = module_from_spec(spec)
                spec.loader.exec_module(module)
                return module
            finally:
                new_modules = set(sys_modules) - set(old_modules)
                for mod in new_modules:
                    del sys_modules[mod]

        def setImportSelfPackageFolder(self, folder: str):
            """
            Yuml核心功能之一
            设置Yuml包导入文件夹
            遍历插件目录，沙箱安全的加载包，同时插件内部仍可使用自身依赖

            :param folder: 包目录
            """
            def reorder_with_priority(original_list, priority_list):
                seen = set()
                result = []

                for item in priority_list:
                    if item in original_list and item not in seen:
                        result.append(item)
                        seen.add(item)

                for item in original_list:
                    if item not in seen:
                        result.append(item)
                        seen.add(item)

                return result
            dir_path = reorder_with_priority(listdir(folder), self.package_sequence)
            for i in dir_path:
                if i.startswith("."):
                    self.window.debug_print(f"忽略包: {i}")
                    continue

                plugin_path = path.join(folder, i)
                module_path = path.join(plugin_path, "main.py")

                if not path.exists(module_path):
                    self.window.error_print(f"无法找到主文件 {i}", "ModuleMainFileNotFound")
                    continue

                unique_module_name = f"plugin_{i}_main"

                with self._temp_sys_path(plugin_path):
                    try:
                        module = self._safe_load_module(unique_module_name, module_path)
                    except Exception as e:
                        self.window.error_print(f"加载插件 `{i}` 失败: {e}", "ModuleLoadError")
                        continue

                if not hasattr(module, "Y_NAMESPACE"):
                    self.window.error_print(f"插件 `{i}` 缺少 Y_NAMESPACE", "ModuleNamespaceError")
                    continue

                base_classes = {
                    module.Y_NAMESPACE.YMainBlock: lambda _obj: self.window.main_block_module.append(_obj),
                    module.Y_NAMESPACE.YWidget: lambda _obj: self.window.widget_block_module.append(_obj),
                    module.Y_NAMESPACE.YLoad: lambda _obj: _obj(self.window),
                    module.Y_NAMESPACE.YWidgetBlock: lambda _obj: self.window.widgetBlock_block_module.append(_obj),
                    module.Y_NAMESPACE.YAddWidgetAttribute:
                        lambda _obj: self.window.widget_add_block_module.append(_obj),
                    module.Y_NAMESPACE.YExport: lambda _obj: self.window.export_module.append(_obj(self.window))
                }

                for name, obj in getmembers(module, isclass):
                    for base, handler in base_classes.items():
                        if issubclass(obj, base) and obj is not base:
                            handler(obj)

            def dedup_class_names(*module_lists):
                _names = set()
                for mod_list in module_lists:
                    for _obj in mod_list:
                        _name = _obj.__name__
                        if _name == "_YuGM_":
                            continue
                        if _name not in _names:
                            _names.add(_name)
                        else:
                            new_name = f"{_name}_{i}"
                            _obj.__name__ = new_name
                            _names.add(new_name)
                            self.window.error_print(f"类名重复 `{_name}`, 强制改名为 `{new_name}`", "ModuleNameError")

            dedup_class_names(
                self.window.main_block_module,
                self.window.widget_block_module,
                self.window.widget_add_block_module,
                self.window.widgetBlock_block_module
            )


        def importPackage(self, *args):
            """
            简单导入 (通过importlib.import_module)
            写上导入的模块名字(字符串)即可

            :param args: 模块名, 空格隔开
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
            :param module_name: 导入的模块, 空格隔开
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
            r"""
            i18n (需通过setI18n配置)
            返回指定名称的翻译文本
            建议赋值为tr (\>tr: app.i18n)

            :param name: 翻译名称
            :return: 翻译文本
            """
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

        def reModuleName(self, name: str, new_name: str):
            """
            重命名模块类名
            无法重命名_YuGM_, 因为他返回的是dict而不是类

            :param name: 原模块类名
            :param new_name: 新的模块类名
            """
            for module_list in [
                self.window.main_block_module,
                self.window.widget_block_module,
                self.window.widget_add_block_module,
                self.window.widgetBlock_block_module]:

                for mod in module_list:
                    if getattr(mod, '__name__', None) == name:
                        mod.__name__ = new_name
                        self.window.debug_print(f"重命名模块 {name} {self.window.Symbols.ASSIGNMENT} {new_name}")
                        return

            raise NameError(f"未找到模块 {name}")

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
                """
                性能监控
                """
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

            # 输入~q退出
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
            """
            if self.window.data.get("lightMode") is not None:
                self.window.call_block("lightMode")

            for i in self.window.findChildren(QWidget):
                i.lightQssStyle(i) if hasattr(i, "lightQssStyle") and callable(getattr(i, 'lightQssStyle')) else None


        def openListenSystemColorMode(self):
            """
            开启监控系统颜色模式功能
            """
            if self._ListenSystemColorTimerModeTimer is None:
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

        def load_export(self, name: str) -> dict | None:
            """
            加载依赖
            :param name: 模块导出ID
            """
            for i in self.window.export_module:
                if i.module_id == name:
                    return i.modules

            return None


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
        def __init__(self, window: "LoadYmlFile"):
            self.notExecBlock = []
            self.window = window

        def notExec(self, block: str):
            """
            不执行特定块的代码
            :param block: 块名
            """
            self.notExecBlock.append(block)

        def execBlockCode(self, block_code: str):
            """
            执行string块
            :param block_code: 块代码
            """
            self.window.exec_code(self.window.yaml.load_str(block_code, True))


    class G:
        def __init__(self, _lua: Lua, _script_g: dict, _eval: dict):
            self.lua = _lua
            self.G = _script_g
            self.eval = _eval
            self._globals = []

        def _update(self, name, value):
            if isinstance(name, list):
                parent = self.getGlobals(name[0])
                for key in name[1:-1]:
                    parent = getattr(parent, key)
                setattr(parent, name[-1], value)
                return
            self.eval[name] = value
            setattr(self.lua.globals(), name, value)
            self.G[name] = value

        def globals(self, name: All | None, value: All) -> All:
            """
            创建全局命名空间
            :param name: 名称
            :param value: 值
            """
            if name is not None:
                self._update(name, value)

            return value

        def updateGlobals(self, name: All, value: All) -> All:
            self._update(name, value)
            for i in self._globals:
                for di, dv in i.items():
                    if di == name:
                        dv(value)

            return value

        def addUpdateList(self, name: All, value) -> All:
            self._globals.append({name: value})
            value(self.getGlobals(name))

            return value

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

        def moveToDataBox(self, name, box):
            ...


class LoadYmlFile(FramelessWindow):  # dev继承自FramelessWindow / build时将它改为继承windowStyle

    class RWidgets:
        def __init__(self, cw: "LoadYmlFile.create_widget"):
            self.createWidget = cw

        def button(self, data, scope, hook):
            self.createWidget("button", data, scope, hook)

        def label(self, data, scope, hook):
            self.createWidget("label", data, scope, hook)

        def listBox(self, data, scope, hook):
            self.createWidget("listBox", data, scope, hook)

        def input(self, data, scope, hook):
            self.createWidget("input", data, scope, hook)

        def yumlWidget(self, data, scope, hook):
            self.createWidget("YUML_WIDGET", data, scope, hook)

        def dynamic(self, data, scope, obj, hook):
            self.createWidget(obj, data, scope, hook)

    class Symbols:
        ASSIGNMENT = "=>"
        RAW = "->>"
        SEPARATION = "--------------------"

    class LoadYAML(YAML):
        def __init__(self, window: "LoadYmlFile" = None):
            super().__init__(typ="rt")
            self.preserve_quotes = True
            self.window = window

        def load_str(self, _str: str, _rep=False) -> dict:
            yaml_str = Template(_str).render()
            data = self.load(yaml_str)
            if not _rep:
                self.window.data = data

            return data

        def load_file(self, file_name, _rep=False):
            if is_sqlite_file(file_name):
                data = SQLiteDict(file_name, "YUML")
                if not _rep:
                    self.window.data = data
            else:
                with open(file_name, "r", encoding="UTF-8") as file:
                    data = self.load(Template(file.read()).render())
                    if not _rep:
                        chdir(dirname(abspath(file_name)))
                        self.window.data = data

            return data


    def __init__(self, file_name: str, app: APPLICATION, load_str: bool = False,
                 is_module: bool = False, _p: QWidget | None = None):
        self.time = perf_counter()
        super().__init__(_p)
        self.version = (0, 0, 0, 1, "beta")
        self.yaml = self.LoadYAML(self)
        self.python = None
        self.NN = lambda x: None
        self.main_block_module = []
        self.widget_block_module = []
        self.widget_add_block_module = []
        self.widgetBlock_block_module = []
        self.export_module = []
        self.execResizeEvent = False
        self.lua = Lua(self)
        self.app = app
        self.titleBar.raise_()
        self._is_create = False
        self.debug_print = self.NN
        self.info_print = self.NN
        self.block = APIS.Block(self)
        self.API_APP = APIS.APP(self.app, self)
        self.lua_api = APIS.Lua(self.lua)
        self._G: dict = {"app": self.API_APP, "Console": APIS.Console(), "Lua": self.lua_api, "block":
                        self.block, "window": super()}
        self.eval_globals = {
            "window": self,
            "app": self.API_APP,
            "Lua": self.lua_api
        }
        self.string_cache = OrderedDict()
        self.STRING_CACHE_LIMIT = 500
        self.string_counter = defaultdict(int)
        self.current_globals = {}
        self.global_args = [self.lua, self._G, self.eval_globals]
        self.API_G = APIS.G(*self.global_args)
        self._G["_G"] = self.API_G
        self.cw = self.RWidgets(self.create_widget)
        self.API_G.globals("YGlobals", self.API_G)
        self.data: dict | SQLiteDict = {}
        if load_str:
            self.yaml.load_str(file_name)
        else:
            self.yaml.load_file(file_name)

        if "template" in self.data:
            warn("template在新版本中被移除, 使用yaml锚点实现相同功能", category=Warns.YuanDeprecatedWarn)

        self.definedDataBox()
        self.definedQss()
        if not is_module:
            for i in self.data["run"]:
                self.main_block(i, "run")
        else:
            for i in self.data["widget"]:
                self.main_block(i, "widget")

    def eval_code(self, code, _locals=None):
        return eval(code, self.eval_globals, _locals if _locals else {})

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
        if scope in self.data:
            for i in self.data[scope]:
                if scope in self.block.notExecBlock:
                    self.block.notExecBlock.remove(scope)
                    return None

                return_value = self.main_block(i, scope, accept)[1]
                if return_value is not None:
                    return return_value
        else:
            self.error_print(f"{scope}未找到", "NoRootBlockError")

        return None

    def widget(self, key: str | dict, data, widget: QWidget, scope: list | str | None, name: str):
        _raw_key = key
        if isinstance(key, dict):
            for i in key:
                data = key[i]
                key = i
                data = {key: data}
        match key:
            case "show":  widget.setVisible(self.string(data[key]))

            case "delGlobals":  self.API_G.delGlobals(self.string(data[key]))

            case "move":
                if isinstance(data[key], list):
                    data = self.process_nested_list(data[key])
                    widget.move(data[0], data[1])
                else:
                    widget.move(self.string(data[key]["x"]), self.string(data[key]["y"]))

            case "size":
                if isinstance(data[key], list):
                    data = self.process_nested_list(data[key])
                    widget.resize(data[0], data[1])
                else:
                    widget.resize(self.string(data[key]["width"]), self.string(data[key]["height"]))

            case "X":  widget.move(self.string(data[key]), widget.y())

            case "Y":  widget.move(widget.x(), self.string(data[key]))

            case "width":  widget.resize(self.string(data[key]), widget.height())

            case "height":  widget.resize(widget.width(), self.string(data[key]))

            case "moveTo":  widget.move(self.eval_code(data[key]).pos())

            case "QssStyle":  widget.setStyleSheet(self.string(data[key]))

            case "id":  widget.setObjectName(self.string(data[key]))

            case "onMoved": widget.installEventFilter(MoveEventFilter(widget, self, data[key]))

            case "styleTo":
                _widget: QWidget = self.eval_code(data[key])
                widget.setStyleSheet(_widget.styleSheet())
                widget.setVisible(_widget.isVisible())
                widget.setObjectName(_widget.objectName())
                widget.resize(_widget.size())

            case "name":
                new_name = self.string(data[key])
                self.API_G.globals(new_name, self.API_G.getGlobals(name))
                self.API_G.delGlobals(name)
                widget.YUML_WIDGET_NAME = new_name

            case "onList":
                self.API_G.getGlobals(self.string(data[key])).append(widget)
                self.API_G.delGlobals(name)

            case "darkStyle":
                setattr(widget, "darkQssStyle", lambda _self, style=self.string(data[key]): _self.setStyleSheet(style))

            case "lightStyle":
                setattr(widget, "lightQssStyle", lambda _self, style=self.string(data[key]): _self.setStyleSheet(style))

            case "parent":
                widget.setParent(self.eval_code(data[key]))

            case _:
                def load_package():
                    _is = None
                    for _i in self.widgetBlock_block_module:
                        if _i.__name__ == key:
                            if _i().attribute(self, data[key], widget) is False:
                                return None
                            _is = True
                            self.debug_print(f"加载Package Widget Block({key} {self.Symbols.RAW} ({_i})")
                    return _is

                if load_package() is None:
                    if scope is not None:
                        _scope = deepcopy(scope)
                        _scope.append(name)
                    else:
                        _scope = None
                    self.main_block(_raw_key, _scope, _is_yuml_widget=True
                    if (isinstance(widget, LoadYmlFile) and key=="type") else False)

    def create_widget(self, widget_type, data, scope, hook):
        def _onClicked(w, v):
            if isinstance(v, str):
                signalCall(w.clicked, lambda _, bid=self.string(v), _w=w: self.clicked(bid, _w, _w))
            else:
                signalCall(w.clicked, lambda _, _v=v: self.exec_code(_v))
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
            "onClicked": _onClicked,
            "items": lambda w, v: [w.addItem(self.string(i)) for i in v],
            "itemOnClicked": lambda w, v: signalCall(w.itemClicked,
                                                     lambda text, bid=self.string(v), _w=w: self.clicked(bid, _w,
                                                                                                   [_w, text])),
            "itemDrag": lambda w, v: w.setDragDropMode(QListWidget.DragDropMode.InternalMove
                                                       if v else QListWidget.DragDropMode.NoDragDrop),
            "textChanged": lambda w, v: signalCall(w.textChanged,
                                                   lambda text, bid=self.string(v), _w=w: self.clicked(bid, _w,
                                                                                                 [_w, text])),
            "placeholderText": lambda w, v: w.setPlaceholderText(self.string(v)),
            "returnPressed": lambda w, v: signalCall(w.returnPressed,
                                                     lambda bid=self.string(v), _w=w: self.clicked(bid, _w,
                                                                                             [_w, _w.text()])),
            "passwordMode": lambda w, v: w.setEchoMode(QLineEdit.EchoMode.Password) if v else None,
        }

        _hook_list = []
        for _i in data:
            _widget = None
            if widget_type == "YUML_WIDGET":
                widget = LoadYmlFile(data[_i]["type"], self.app, _p=self, is_module=True)
            else:
                widget = widget_creators.get(widget_type, lambda: None)()
            if not widget:
                _widget = widget_type(self)
                widget_type = widget_type.__name__
                widget = _widget.widget

            setattr(widget, "YUML_WIDGET_NAME", _i)
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

                if scope is not None:
                    _scope = [scope, widget_type] if isinstance(scope, str) else deepcopy(scope).append(widget_type)
                else:
                    _scope = None
                    key = {key: val}
                self.widget(key, data[_i], widget, _scope, widget.YUML_WIDGET_NAME)

            _hook_list.append(widget)

        self.set_hook(hook, _hook_list)

    def set_hook(self, hook, value):
        if hook is not None:
            if isinstance(hook, list):
                hook.append(value)
            else:
                self.API_G.globals(hook, value)

    def get_all_hooks(self, data):
        hooks = []
        self.exec_code(data, hook=hooks)
        return hooks

    def exec_code(self, value: dict, *args, **kw):
        for i, v in value.items():
            msg = self.main_block({i: v}, *args, **kw)[0]
            if msg:
                return msg

        return None

    def main_block(self, block_name: str | dict, scope: str | list | None = None,
                   _accept=None, _is_yuml_widget = False, hook = None, _wh = None) -> tuple:
        return_value = None
        info = None
        if hook:
            if not isinstance(hook, list):
                # 处理hook但main_block没有返回值的情况
                self.set_hook(hook, None)

        if not isinstance(block_name, dict):
            blocks = block_name.split("_")
        else:
            blocks = next(iter(block_name)).split("_")
        _block_name = blocks[0]
        def rep():
            nonlocal _block_name
            if not isinstance(block_name, dict):
                _block_name = block_name
            else:
                _block_name = next(iter(block_name))
        if len(blocks) > 2:
            self.debug_print(f"{block_name} `_` 数量超过1(自动跳过)")
            rep()

        try:
            int(blocks[1])

        except ValueError:
            self.debug_print(f"{block_name} `_` 后不是数字(自动跳过)")
            rep()

        except IndexError:
            pass

        if not isinstance(block_name, dict):
            if isinstance(scope, list):
                data = self.data
                for i in scope:
                    data = data[i]
                data = data[block_name]
            else:
                data = self.data[scope][block_name]
        else:
            data = next(iter(block_name.values()))
            block_name = next(iter(block_name))

        self.debug_print(f"{block_name} 去除`_`: {_block_name} ({scope})")

        match _block_name:
            case "windowSize":
                if isinstance(data, list):
                    data = self.process_nested_list(data)
                    self.resize(data[0], data[1])
                else:
                    self.resize(self.string(data["width"]), self.string(data["height"]))
            case "windowTitle":
                self.setWindowTitle(self.string(data))
            case "windowIcon":
                self.setWindowIcon(QIcon(self.string(data)))
            case "globalStyle":
                self.setStyleSheet(self.string(data))
            case "button":
                self.cw.button(data, scope, hook)
            case "label":
                self.cw.label(data, scope, hook)
            case "listBox":
                self.cw.listBox(data, scope, hook)
            case "input":
                self.cw.input(data, scope, hook)
            case "YUML_WIDGET":
                self.cw.yumlWidget(data, scope, hook)
            case "box":
                boxs = []
                for i, v in data.items():
                    box = QWidget(self)
                    self.API_G.globals(i, box)
                    boxs.append(box)
                    hooks = self.get_all_hooks(v)

                    for widget_list in hooks:  # [[<WidgetType1>, <WidgetType1>], [<WidgetType2>, ...]]
                        if isinstance(widget_list, list):
                            for widget in widget_list:
                                if isinstance(widget, QWidget):
                                    pos = widget.pos()
                                    is_show = widget.isVisible()
                                    widget.setParent(box)
                                    widget.move(pos)
                                    widget.setVisible(is_show)

                    box.show()

                self.set_hook(hook, boxs)
            case "HOOK":
                for name, value in data.items():
                    self.exec_code(value, hook=name)
            case "RETURN":
                return_value = self.string(data)
            case "LOG":
                if isinstance(data, list):
                    _args = self.process_nested_list(data)
                    print(_args[0], **_args[1])
                else:
                    print(self.string(data))
            case "CONTINUE":
                if _wh:
                    info = f"{_wh}-CONTINUE"
            case "BREAK":
                if _wh:
                    info = f"{_wh}-BREAK"
            case "WHILE":
                is_break = False
                try:
                    cond = self.eval_code(data["COND"])
                except TypeError:
                    cond = data["COND"]
                while cond:
                    for _i, _v in data["CODE"].items():
                        msg = self.main_block({_i: _v}, _wh="WHILE")[0]
                        if msg == "WHILE-CONTINUE":
                            break
                        elif msg == "WHILE-BREAK":
                            is_break = True
                            break

                    if is_break:
                        break
                else:
                    _else = data.get("ELSE")
                    if _else:
                        self.exec_code(_else, _wh=_wh)
            case "FOR":
                cond = self.eval_code(data["ITER"])
                name = self.string(data.get("NAME"))
                is_break = False
                is_continue = False
                for i in cond:
                    self.API_G.globals(name, i) if name else None
                    for _i, v in data["CODE"].items():  # 这里不用self.exec_code()
                        msg = self.main_block({_i: v}, _wh="FOR")[0]
                        if msg == "FOR-CONTINUE":
                            is_continue = True
                            break
                        elif msg == "FOR-BREAK":
                            is_break = True
                            break
                    else:
                        _else = data.get("ELSE")
                        if _else:
                            self.exec_code(_else, _wh=_wh)

                    if is_break:
                        break
                    if is_continue:
                        is_continue = False
                        continue
            case "DELETE":
                for i in self.process_nested_list(data):
                    self.API_G.delGlobals(i)
            case "LOCAL":
                _vars: list = self.process_nested_list(data["VARS"])
                self.exec_code(data["CODE"])
                _hook = []
                for i in _vars:
                    _hook.append({i: self.API_G.getGlobals(i)})
                    self.API_G.delGlobals(i)
                self.set_hook(hook, _hook)
            case "IF":
                for i in data:
                    if i != "ELSE":
                        if self.eval_code(i):
                            info = self.exec_code(data[i], _wh=_wh)
                            break
                else:
                    if data.get("ELSE"):
                        info = self.exec_code(data["ELSE"], _wh=_wh)
            case "YuanGuiScript":
                Script(data, self._G)
            case "LuaScript":
                self.lua.execute(data)
            case "QssStyle":
                self.setStyleSheet(self.string(data))
            case "callBlock":
                for i in [[self.string(x) for x in _list] for _list in data]:
                    self.set_hook(hook, self.call_block(*i))
            case "CALL_BLOCK":
                if isinstance(data, str):
                    self.set_hook(hook, self.call_block(self.string(data)))
                else:
                    data = self.process_nested_list(data)
                    self.set_hook(hook, self.call_block(*data))
            case "PythonScript":
                if isinstance(data, list):
                    value = self.eval_code(data[0])
                elif isinstance(data, str):
                    exec(data, self.eval_globals)
                    value = None
                else:
                    self.error_print("PythonScript仅支持字符串或列表", "PythonScriptTypeError")
                    value = None

                self.set_hook(hook, value)
            case "IMPORT":
                self.API_APP.setImportSelfPackageFolder(self.string(data))

            case _:
                raw = block_name
                self.debug_print(f"未找到默认block, 已将block替换为原名({_block_name} {self.Symbols.ASSIGNMENT} {raw})")

                def load_package():
                    for modules, handler in [
                        (self.main_block_module, lambda _mod: _mod(data, hook, self)),
                        (self.widget_block_module, lambda _mod: self.cw.dynamic(data, scope, _mod, hook))]:
                        for mod in modules:
                            if mod.__name__ == raw:
                                handler(mod)
                                block_type = "Block" if modules is self.main_block_module else "Widget"
                                self.debug_print(f"加载Package {block_type}({raw} {self.Symbols.RAW} {mod})")
                                return True
                    return None

                if block_name[0] not in ["\\", "$"]:
                    block_name = block_name.split("<")
                    if len(block_name) != 1:
                        for i in block_name[1:]:
                            if i == "notExec":
                                break
                            else:
                                self.error_print(f"`{i}`操作不存在", "NoCommandError")

                    else:
                        if load_package() is None:
                            if not _is_yuml_widget:
                                self.error_print(f"没有名为`{block_name[0]}`的元素", "NoBlockError")

                else:
                    if block_name[0] == "\\":
                        block_name = block_name[1:]
                        block = block_name[1:]
                        match block_name[0]:
                            case "=":
                                self.API_G.globals(block, self.string(data))
                            case ">":
                                if data == ".accept":
                                    self.API_G.globals(block, _accept)
                                else:
                                    if block[0] == ">":
                                        gl = self.API_G.updateGlobals
                                        block = block[1:]
                                        _path = block.split("::")
                                        if len(_path) > 1:
                                            block = _path
                                    else:
                                        gl = self.API_G.globals

                                    if isinstance(data, str):
                                        gl(block, self.eval_code(data))
                                    else:
                                        gl(block, data)
                            case "#":
                                # HOOK的另一种写法
                                self.exec_code(data, hook=block)

                    elif block_name[0] == "$":
                        data = self.process_nested_list(data)
                        _path = block_name[1:].split("::")
                        _is_exec = True
                        if _path[0][0] == "|":
                            func = self.API_G.getGlobals(_path[0][1:])
                            if func is None:
                                _is_exec = False
                        else:
                            func = self.API_G.getGlobals(_path[0])

                        if _is_exec:
                            if len(_path) != 1:
                                func = reduce(getattr, _path[1:], func)
                                if data is None:
                                    value = func
                                else:
                                    data: All
                                    data = self.process_nested_list(data)
                                    value = func(*data[0], **data[1])
                            else:
                                value = func(*data[0], **data[1])
                            self.set_hook(hook, value)

        self.titleBar.raise_()
        return info, return_value

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

    def definedDataBox(self):
        class DataBox:
            pass

        data: dict = self.data.get("dataBox")
        if data:
            for i, v in data.items():
                data_box = DataBox()
                self.API_G.globals(i, data_box)
                if v:
                    for di, dv in v.items():
                        setattr(data_box, di, dv)

    def process_nested_list(self, data) -> All:
        if isinstance(data, list):
            return [self.process_nested_list(item) for item in data]
        elif isinstance(data, dict):
            return {
                self.string(key): self.process_nested_list(value)
                for key, value in data.items()
            }
        else:
            return self.string(data)

    def showEvent(self, a0):
        super().showEvent(a0)
        if self._is_create:
            if self.data.get("windowShowed"):
                self.call_block("windowShowed")
            return

        self._is_create = True

        if self.data.get("windowCreated"):
            self.call_block("windowCreated")
            current = perf_counter()
            self.info_print(f"启动用时: {current - self.time} {self.Symbols.RAW} "
                            f"({current - start_time})\n{self.Symbols.SEPARATION}\n")

    def resizeEvent(self, a0):
        super().resizeEvent(a0)
        if not self.execResizeEvent:
            self.execResizeEvent = True  # PyQt第一次创建窗口时, 会调用resizeEvent, 屏蔽第一次创建窗口事件
            return

        if self.data.get("windowResized"):
            self.call_block("windowResized")

    def hideEvent(self, a0):
        if self.data.get("windowHidden"):
            self.call_block("windowHidden")

    def moveEvent(self, a0):
        super().moveEvent(a0)
        if getattr(self, "data", None):
            if self.data.get("windowMoved"):
                self.call_block("windowMoved")

    def closeEvent(self, event):
        setattr(event, "Yes", event.accept)
        setattr(event, "No", event.ignore)
        if self.data.get("windowClosed"):
            self.call_block("windowClosed", event)
        else:
            super().closeEvent(event)
            event.accept()

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

    def string(self, s) -> All:
        """
        Yuml核心功能之一
        字符串渲染引擎

        将{<>}内部的代码使用eval执行并返回结果
        默认返回为字符串
        若为:obj, 则返回eval结果
        若为:int, 则返回eval结果转换为int

        示例:
        {< 1 + 1 >} -> '2'
        {< 1 + 1 >} :int -> 2
        {< 1 + 1 >} :obj -> 2

        不会再增加更多的类型转换, 会导致代码可读性降低, 完全可以通过:obj代替
        如:
        bool:
        {< True >} :obj -> True
        {< float(1) >} :obj -> 1.0 你可以用:obj + 代码进行类型转换

        {< MyClass() >} -> 'MyClass' 对象的字符串表示
        {< MyClass() >} :obj -> MyClass对象本身
        {< MyClass() >} :int -> ValueError

        若为:
        {<< 1+1 >>}将会被替换为{<1+1>}, 并不会被执行, 类似python的f-string的{{}}一样会被替换为{}, 例如:
            {< 1+1 >} ::int -> '2 :int'
            {< 1+1 >} :int -> 2
            {<< 1+1 >>} :int -> '{<1+1>} :int'
            {<< 1+1 >>} ::int -> '{<1+1>} ::int'
            {<<    1+1       >>} -> '{<1+1>}' 会舍弃外围空格
            {<<    1 + 1       >>} -> '{<1 + 1>}' 不会舍弃内部空格
        若:int为::int, 则会替换为:int并且不会被执行
        :obj同上

        如果:
        {< a >} {< b >} :obj -> b
        若为:obj, 且{<>}转译数量>1, 会默认返回最后的结果
        {< 1 >}{< 2 >} :int -> 12
        若为:int, 则先计算字符串渲染的结果, 然后在转换为int
        示例:
            {< 1 >}{< 2 >} :int -> 12
            {< 1 >} {< 2 >} :int -> ValueError 因为带空格, 相当于int("1 2")
            {< 1 >}{< 2 >} :obj -> 2
            {< 1 >} {< 2 >} :obj -> 2 默认返回最后一个
            {< True >} {< False >} :obj -> False
            hello {< name >} {< '!' >} :obj -> '!'
            {< name >}, hello{< '!' >} :obj -> '!'
        """

        if not isinstance(s, str):
            return s

        if s in self.string_cache:
            self.string_cache.move_to_end(s)
            return self.string_cache[s](self.current_globals)

        self.string_counter[s] += 1
        if self.string_counter[s] > 3:
            try:
                func = self._compile_string_to_lambda(s)
                self.string_cache[s] = func
                self.string_cache.move_to_end(s)
                if len(self.string_cache) > self.STRING_CACHE_LIMIT:
                    self.string_cache.popitem(last=False)
                return func(self.current_globals)
            except Exception as e:
                self.error_print(e, "JITCompileError")

        is_rep = False
        eval_result = None

        def rep(m):
            nonlocal is_rep, eval_result
            try:
                is_rep = True
                eval_result = self.eval_code(m.group(1).strip())
                return str(eval_result)
            except Exception as error:
                self.error_print(error, "StringError")
                return ""

        is__rep = False

        def _rep(m):
            nonlocal is__rep
            is__rep = True
            return '{<' + m.group(1).strip() + '>}'

        _str = sub(r'\{<<\s*(.*?)\s*>>}', _rep, s)

        if not is__rep:
            _str = sub(r'\{<\s*([^>]+?)\s*>}', rep, _str)

        if not is_rep:
            return _str

        try:
            s = _str[:-5] + _str[-4:]
            if _str.endswith(":int"):
                return_value = int(_str[:-4]) if _str[-5] != ":" else s
            elif _str.endswith(":obj"):
                return_value = eval_result if _str[-5] != ":" else s
            else:
                return_value = _str
        except IndexError:
            return_value = _str

        return return_value

    def _compile_string_to_lambda(self, s: str):
        if s.endswith("::int") or s.endswith("::obj"):
            return lambda ctx: s[:-5] + s[-4:]

        render_type = None
        if s.endswith(":int"):
            render_type = "int"
            s = s[:-4]
        elif s.endswith(":obj"):
            render_type = "obj"
            s = s[:-4]

        exprs = []
        last_expr = None
        last_pos = 0
        pattern = r'\{<\s*(.*?)\s*>}'
        for match in finditer(pattern, s):
            start, end = match.span()
            text = s[last_pos:start]
            if text:
                exprs.append(repr(text))
            code = match.group(1).strip()
            exprs.append(f'str(eval_code("{code}", ctx))')
            last_expr = code
            last_pos = end

        if last_pos < len(s):
            exprs.append(repr(s[last_pos:]))

        joined = '"".join([' + ', '.join(exprs) + '])'
        func = eval(f'lambda ctx: {joined}', {'eval_code': self.eval_code})

        if render_type == "int":
            return lambda ctx: int(func(ctx))
        elif render_type == "obj":
            if last_expr:
                return lambda ctx: self.eval_code(last_expr, ctx)
            else:
                return lambda ctx: None
        else:
            return lambda ctx: str(func(ctx))


if __name__ == '__main__':
    print("请打开`demos`目录查看示例")
