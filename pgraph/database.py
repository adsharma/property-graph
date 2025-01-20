from typing import List

from fquery.sqlmodel import GLOBAL_ID_SEQ
from sqlalchemy import create_engine, func
from sqlmodel import Session

DATABASE_URL = "duckdb:///pgraph.db"

engine = create_engine(DATABASE_URL, echo=True)


def allocate_ids(n) -> List[int] | None:
    ids = None
    with engine.connect() as conn:
        ids = [conn.execute(func.next_value(GLOBAL_ID_SEQ)).scalar() for _ in range(n)]
    return ids


class Database:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
            cls._instance.db = Session(engine)
        return cls._instance
