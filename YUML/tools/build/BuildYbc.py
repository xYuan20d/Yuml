from YUML.data.YSQLite import dict_to_sqlite
from YUML.Yuml import LoadYmlFile

def buildToYbc(yuml_file_name: str, ybc_file_name: str = None):
    if ybc_file_name is None:
        ybc_file_name = yuml_file_name + ".ybc"
    data = LoadYmlFile.LoadYAML().load_file(yuml_file_name, True)
    dict_to_sqlite(data, ybc_file_name, "YUML")
