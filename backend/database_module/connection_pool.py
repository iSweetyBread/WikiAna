import psycopg2.pool as pgp
from contextlib import contextmanager
from config import load_config

_pool = pgp.ThreadedConnectionPool(1, 32, **load_config())

@contextmanager
def get_conn():
    conn = _pool.getconn()
    
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        _pool.putconn(conn)