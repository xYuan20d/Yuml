import sqlite3
import json
from typing import Any, Iterator, Optional, Dict


class SQLiteDict:
    def __init__(self, db_path: str, table: str = "kv_store"):
        self.db_path = db_path
        self.table = table
        self._conn = sqlite3.connect(self.db_path)
        self._conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {self.table} (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
        """)
        self._conn.commit()

    def __setitem__(self, key: str, value: Any):
        val_str = json.dumps(value)
        self._conn.execute(
            f"INSERT INTO {self.table} (key, value) VALUES (?, ?) "
            f"ON CONFLICT(key) DO UPDATE SET value=excluded.value;",
            (key, val_str)
        )
        self._conn.commit()

    def __getitem__(self, key: str) -> Any:
        cur = self._conn.execute(
            f"SELECT value FROM {self.table} WHERE key=?;", (key,)
        )
        row = cur.fetchone()
        if row is None:
            raise KeyError(f"Key {key} not found")
        return json.loads(row[0])

    def __delitem__(self, key: str):
        cur = self._conn.execute(
            f"DELETE FROM {self.table} WHERE key=?;", (key,)
        )
        if cur.rowcount == 0:
            raise KeyError(f"Key {key} not found")
        self._conn.commit()

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        try:
            return self[key]
        except KeyError:
            return default

    def keys(self) -> Iterator[str]:
        cur = self._conn.execute(f"SELECT key FROM {self.table};")
        for row in cur:
            yield row[0]

    def values(self) -> Iterator[Any]:
        cur = self._conn.execute(f"SELECT value FROM {self.table};")
        for row in cur:
            yield json.loads(row[0])

    def items(self) -> Iterator[tuple[str, Any]]:
        cur = self._conn.execute(f"SELECT key, value FROM {self.table};")
        for key, val_str in cur:
            yield key, json.loads(val_str)

    def update(self, data: dict):
        # 批量插入/更新
        with self._conn:
            for key, value in data.items():
                val_str = json.dumps(value)
                self._conn.execute(
                    f"INSERT INTO {self.table} (key, value) VALUES (?, ?) "
                    f"ON CONFLICT(key) DO UPDATE SET value=excluded.value;",
                    (key, val_str)
                )

    def clear(self):
        self._conn.execute(f"DELETE FROM {self.table};")
        self._conn.commit()

    def __contains__(self, key: str) -> bool:
        cur = self._conn.execute(
            f"SELECT 1 FROM {self.table} WHERE key=? LIMIT 1;", (key,)
        )
        return cur.fetchone() is not None

    def __str__(self):
        return str(dict(self.items()))

    def __repr__(self):
        return  self.__str__()

    def close(self):
        self._conn.close()


def dict_to_sqlite(data: Dict[str, Any], db_path: str, table_name: str = "kv_store"):
    # 连接数据库，文件不存在则创建
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # 建表（如果存在则删除旧表，确保覆盖）
    cur.execute(f"DROP TABLE IF EXISTS {table_name};")
    cur.execute(f"""
        CREATE TABLE {table_name} (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
    """)

    # 准备批量插入
    items = [(key, json.dumps(value)) for key, value in data.items()]

    # 插入数据
    cur.executemany(
        f"INSERT INTO {table_name} (key, value) VALUES (?, ?);",
        items
    )

    conn.commit()
    conn.close()

def is_sqlite_file(path: str) -> bool:
    with open(path, 'rb') as f:
        header = f.read(16)
    return header == b'SQLite format 3\x00'


if __name__ == '__main__':
    dict_to_sqlite(
        {"test": {"a": [3.0, 2.0, 1.00]},
        "test2": {"b": [1, 2, 3]}}
        , "test.db")
    if is_sqlite_file("test.db"):
        db = SQLiteDict("test.db")
        print(db)