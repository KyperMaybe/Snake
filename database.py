import pyodbc
from config import DB_BASE, DB_PORTS, TOP_LIMIT

_working_port: int | None = None


def _conn_str(port: int) -> str:
    return (
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={DB_BASE['host']},{port};"
        f"DATABASE={DB_BASE['database']};"
        f"UID={DB_BASE['username']};"
        f"PWD={DB_BASE['password']};"
        f"TrustServerCertificate=yes;"
    )


def _try_connect(port: int, timeout: int = 2):
    try:
        return pyodbc.connect(_conn_str(port), timeout=timeout)
    except Exception as exc:
        print(f"[DB] Порт {port} не отвечает: {exc}")
        return None


def _find_working_connection():
    global _working_port

    if _working_port is not None:
        conn = _try_connect(_working_port, timeout=2)
        if conn is not None:
            print(f"[DB] Подключение к порту {_working_port} (из кэша)")
            return conn
        print(f"[DB] Порт {_working_port} перестал работать, ищу заново")
        _working_port = None

    for port in DB_PORTS:
        conn = _try_connect(port, timeout=2)
        if conn is not None:
            _working_port = port
            print(f"[DB] Подключение к порту {port} (найден)")
            return conn

    raise ConnectionError(
        "Не удалось подключиться ни к одному порту. "
        "Проверьте, запущен ли fxtun."
    )


def warm_up() -> bool:
    try:
        conn = _find_working_connection()
        conn.close()
        print(f"[DB] Готово к работе, порт {_working_port}")
        return True
    except ConnectionError as exc:
        print(f"[DB] ВНИМАНИЕ: {exc}")
        return False


def save_and_fetch(player_name: str, score: int):
    conn = _find_working_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO Scores (PlayerName, Score, GameDate) "
            "VALUES (?, ?, GETDATE())",
            (player_name, score),
        )
        cur.execute(
            f"SELECT TOP {TOP_LIMIT} PlayerName, Score FROM Scores "
            "ORDER BY Score DESC, GameDate ASC"
        )
        top = [(r[0], r[1]) for r in cur.fetchall()]

        cur.execute("SELECT COUNT(*) FROM Scores WHERE Score > ?", (score,))
        r = cur.fetchone()
        rank = (r[0] if r else 0) + 1

        cur.execute("SELECT COUNT(*) FROM Scores")
        r = cur.fetchone()
        total = r[0] if r else 0

        conn.commit()
        return top, rank, total
    finally:
        conn.close()