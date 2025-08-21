import sqlite3
from contextlib import contextmanager
from pathlib import Path

DB_PATH = Path(__file__).parent / "monitor.db"


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.executescript(
        """
    PRAGMA foreign_keys=ON;
    create table if not exists sessions(
        token text primary key,
        credits integer not null default 0,
        created real not null,
        last_used real
    );
    create table if not exists canonical_targets(
        cid text primary key,
        url text not null,
        fingerprint text,
        probe_type text default 'http',
        last_probe real,
        last_ok integer default 0,
        next_run real
    );
    create table if not exists watchers(
        wid text primary key,
        cid text not null references canonical_targets(cid) on delete cascade,
        token text not null references sessions(token) on delete cascade,
        interval integer not null,
        enabled integer default 1,
        created real
    );
    create table if not exists ledger(
        id integer primary key autoincrement,
        ts real,
        action text,
        token text,
        cid text,
        wid text,
        amount integer,
        balance integer,
        note text
    );
    """
    )
    conn.commit()
    conn.close()


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()
