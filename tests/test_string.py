import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from YUML.Yuml import LoadYmlFile, APPLICATION
main = LoadYmlFile("", APPLICATION([]), load_str=True, _mode="test")

def test_basic_eval():
    assert main.string("{< 1 + 1 >}") == "2"
    assert main.string("{< 1 + 1 >} :int") == 2
    assert main.string("{< 1 + 1 >} :obj") == 2

def test_type_coercion():
    assert main.string("{< True >} :obj") is True
    assert main.string("{< float(2) >} :obj") == 2.0

def test_escape_behavior():
    assert main.string("{<< 1+1 >>}") == "{<1+1>}"
    assert main.string("{<< 1+1 >>} :int") == "{<1+1>} :int"
    assert main.string("{<< 1+1 >>} ::int") == "{<1+1>} ::int"
    assert main.string("{<<  1+1  >>}") == "{<1+1>}"
    assert main.string("{<<  1 + 1  >>}") == "{<1 + 1>}"

def test_obj_and_int_behavior_multi_expr():
    assert main.string("{< 1 >}{< 2 >} :int") == 12
    assert main.string("{< 1 >} {< 2 >} :obj") == 2
    assert main.string("{< 1 >}{< 2 >} :obj") == 2
    assert main.string("{< True >} {< False >} :obj") is False

def test_string_concat_vs_obj_last():
    main.current_globals["name"] = "world"
    assert main.string("hello {< name >} {< '!' >} :obj") == "!"
    assert main.string("{< name >}, hello{< '!' >} :obj") == "!"

def test_compile_cache_trigger():
    # 模拟多次调用同一表达式触发 JIT 缓存机制（>3 次）
    expr = "{< 3 * 3 >}"
    for _ in range(4):
        result = main.string(expr)
    assert result == "9"

def test_invalid_eval_handling():
    result = main.string("{< 1 / 0 >}")
    assert result == ""  # 遇到异常返回空串
    result = main.string("{< MyClass() >} :int")
    assert isinstance(result, str)  # 会抛异常，进入 except，返回字符串或空串