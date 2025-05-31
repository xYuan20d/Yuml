from sys import stderr
import re


class Script:
    """
    完整的脚本解释器实现
    语法说明：
    - 变量赋值：=:变量名=值（支持表达式）
    - 方法调用：$对象|方法: 参数（支持类型标注）
    - 条件执行：? 条件表达式 => 执行动作
    - 注释：-: 注释内容
    - 变量引用：$变量名
    - 函数定义：&函数名(参数) => 执行内容
    - 函数调用：&函数名(参数) => 执行内容
    """

    class ExitException(BaseException):
        """自定义退出异常"""
        pass

    def __init__(self, code: str, _globals: dict = None):
        self.code = code
        self.globals = _globals if _globals is not None else {}
        self.functions = {}  # 用于存储函数定义
        self.exec()

    def exec(self):
        """执行入口"""
        try:
            for line in self.code.splitlines():
                self._process_line(line.strip())
        except self.ExitException:
            pass  # 静默退出

    def _process_line(self, line: str):
        """处理单行代码"""
        if not line:
            return

        # 退出命令检测
        if line == "\\exit":
            raise self.ExitException()

        try:
            if line.startswith("$"):
                self._handle_method_call(line[1:])
            elif line.startswith("=:"):
                self._handle_assignment(line[2:])
            elif line.startswith("-:"):
                pass  # 跳过注释
            elif line.startswith("?"):
                self._handle_condition(line[1:].strip())
            elif line.startswith("&"):
                self._handle_function_definition(line[1:])
            else:
                self._handle_variable_usage(line)
        except self.ExitException:  # 透传退出异常
            raise
        except Exception as e:
            print(f"执行错误: {e}", file=stderr)

    def _evaluate_expression(self, expr: str):
        """表达式求值（支持变量和运算符）"""
        var_pattern = re.compile(r'\$([a-zA-Z_]\w*)')

        def var_replacer(match):
            var_name = match.group(1)
            value = self.globals.get(var_name)
            if value is None:
                raise NameError(f"变量 '{var_name}' 未定义")
            return repr(value)

        try:
            # 替换变量并求值
            substituted = var_pattern.sub(var_replacer, expr)
            return eval(substituted, {"__builtins__": None}, {})
        except Exception as e:
            raise ValueError(f"表达式错误: '{expr}' ({e})")

    def _handle_function_definition(self, line: str):
        """处理函数定义"""
        if '=>' not in line:
            raise SyntaxError("函数定义格式错误，缺少 => 分隔符")

        func_header, body = line.split('=>', 1)
        func_header = func_header.strip()
        body = body.strip()

        if '(' not in func_header or ')' not in func_header:
            raise SyntaxError("函数定义格式错误，缺少括号")

        func_name, param_str = func_header.split('(', 1)
        param_str = param_str.strip().rstrip(')')
        func_name = func_name.strip()

        params = [param.strip() for param in param_str.split(',')] if param_str else []
        self.functions[func_name] = {"params": params, "body": body}

    def _handle_function_call(self, line: str):
        """处理函数调用"""
        if '(' not in line or ')' not in line:
            raise SyntaxError("函数调用格式错误，缺少括号")

        func_name, param_str = line.split('(', 1)
        param_str = param_str.strip().rstrip(')')
        func_name = func_name.strip()

        params = [param.strip() for param in param_str.split(',')] if param_str else []

        if func_name in self.functions:
            func = self.functions[func_name]
            if len(params) != len(func["params"]):
                raise SyntaxError(f"函数 {func_name} 的参数数量不匹配")

            # 处理函数体内的代码
            self._process_function_body(func_name, params, func["body"])
        else:
            raise NameError(f"函数 '{func_name}' 未定义")

    def _process_function_body(self, func_name: str, params: list, body: str):
        """执行函数体"""
        # 先保存当前的全局变量
        saved_globals = self.globals.copy()

        # 将参数赋值到全局变量
        for param, value in zip(self.functions[func_name]["params"], params):
            self.globals[param] = self._evaluate_expression(value)

        # 解析并执行函数体
        for line in body.splitlines():
            self._process_line(line.strip())

        # 恢复全局变量
        self.globals = saved_globals

    def _handle_condition(self, line: str):
        """处理条件语句"""
        if '=>' not in line:
            raise SyntaxError("条件语句格式错误，缺少 => 分隔符")

        condition, action = line.split('=>', 1)
        condition = condition.strip()
        action = action.strip()

        try:
            if self._evaluate_expression(condition):
                self._process_line(action)
        except Exception as e:
            print(f"条件执行失败: {e}", file=stderr)

    def _handle_method_call(self, line: str):
        """处理方法调用（支持返回值赋值）"""
        method_part, assign_part = self._split_assignment(line)

        if "|" not in method_part:
            raise SyntaxError("方法调用格式错误，缺少 | 分隔符")

        obj_part, rest = method_part.split("|", 1)
        obj_name = obj_part.strip()
        target = self.globals.get(obj_name)

        if target is None:
            raise NameError(f"对象 '{obj_name}' 未定义")

        # 解析方法和参数
        method_name, *args_part = rest.split(":", 1)
        method_name = method_name.strip()
        args_str = args_part[0].strip() if args_part else ""

        # 获取方法对象
        method = getattr(target, method_name, None)
        if not callable(method):
            raise AttributeError(f"方法 '{method_name}' 不存在或不可调用")

        # 解析参数并执行
        args = self._parse_arguments(args_str)
        return_value = method(*args)  # 获取返回值

        # 处理返回值赋值
        if assign_part:
            if assign_part.startswith("=:"):
                var_name = assign_part[2:].strip()
                self.globals[var_name] = return_value
            else:
                raise SyntaxError("返回值赋值格式错误，应为 => =:变量名")

    def _split_assignment(self, line: str):
        """安全分割方法调用和返回值赋值部分"""
        in_quote = None
        escaped = False
        for i, c in enumerate(line):
            if escaped:
                escaped = False
                continue
            if c == '\\':
                escaped = True
            elif c in ('"', "'"):
                if in_quote == c:
                    in_quote = None
                else:
                    in_quote = c
            elif c == '=' and i < len(line) - 1 and line[i + 1] == '>' and not in_quote:
                return line[:i].strip(), line[i + 2:].strip()
        return line, None

    def _parse_arguments(self, args_str: str) -> list:
        """解析参数（支持类型标注和嵌套表达式）"""
        if not args_str:
            return []

        args = []
        for arg in self._split_args(args_str):
            arg = arg.strip()
            if not arg:
                continue

            # 处理类型标注
            value_part, _, type_hint = arg.partition('//')
            value_str = value_part.strip()
            type_name = type_hint.strip().lower()

            try:
                value = self._evaluate_expression(value_str)
                if type_name:
                    value = self._convert_type(value, type_name)
                args.append(value)
            except Exception as e:
                print(f"参数解析失败: {arg} ({e})", file=stderr)
                args.append(None)

        return args

    def _convert_type(self, value, type_name: str):
        """类型转换处理"""
        converters = {
            'int': int,
            'float': float,
            'str': str,
            'bool': lambda x: bool(int(x)),
        }

        if type_name not in converters:
            raise ValueError(f"不支持的类型转换: {type_name}")

        try:
            return converters[type_name](value)
        except (ValueError, TypeError) as e:
            raise ValueError(f"类型转换失败: {value} -> {type_name} ({e})")

    def _split_args(self, s: str) -> list:
        """高级参数分割（支持引号和转义）"""
        args = []
        buffer = []
        in_quote = None
        escaped = False

        for char in s:
            if escaped:
                buffer.append(char)
                escaped = False
            elif char == '\\':
                escaped = True
            elif in_quote:
                if char == in_quote:
                    in_quote = None
                buffer.append(char)
            else:
                if char in ('"', "'"):
                    in_quote = char
                    buffer.append(char)
                elif char == ',':
                    args.append(''.join(buffer).strip())
                    buffer = []
                else:
                    buffer.append(char)

        if buffer:
            args.append(''.join(buffer).strip())
        return args

    def _handle_assignment(self, line: str):
        """处理变量赋值"""
        if '=' not in line:
            raise SyntaxError("赋值语句缺少等号")

        var_name, value_str = line.split('=', 1)
        var_name = var_name.strip()
        value_str = value_str.strip()

        try:
            value = self._evaluate_expression(value_str)
            self.globals[var_name] = value
        except Exception as e:
            print(f"赋值失败: {var_name} = {value_str} ({e})", file=stderr)

    def _handle_variable_usage(self, var_name: str):
        """处理变量使用"""
        if var_name in self.globals:
            print(f"{var_name} = {self.globals[var_name]}")
        else:
            print(f"错误: 未定义的变量 '{var_name}'", file=stderr)


if __name__ == "__main__":
    demo_code = """
    &main(a, b) => 
        =:result = $a + $b
        $sys|print: "结果是：", $result
    &main(3, 5)
    """

    class SystemAPI:
        def print(self, *args):
            print(*args)

    Script(demo_code, {
        "sys": SystemAPI(),
        "__builtins__": None
    })
