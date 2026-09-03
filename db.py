import os

from dotenv import load_dotenv
from sqlalchemy import Column, Identity, Integer, String, create_engine
from sqlalchemy.orm import DeclarativeBase

# Connection settings, shared by the app and by Alembic (see alembic/env.py)
load_dotenv(".env")
DBUSER = os.environ["DBUSER"]
DBPASS = os.environ["DBPASS"]
DBHOST = os.environ["DBHOST"]
DBNAME = os.environ["DBNAME"]
# Postgres schema the tables live in; defaults to the standard "public"
DBSCHEMA = os.environ.get("DBSCHEMA", "public")


def get_database_uri() -> str:
    uri = f"postgresql://{DBUSER}:{DBPASS}@{DBHOST}/{DBNAME}"
    if DBHOST != "localhost":
        uri += "?sslmode=require"
    return uri


def get_connect_args() -> dict:
    # Point search_path at DBSCHEMA so unqualified table names resolve there.
    # This keeps the models and the migrations free of a hard-coded schema name.
    return {"options": f"-csearch_path={DBSCHEMA}"}


def create_db_engine(**kwargs):
    return create_engine(get_database_uri(), connect_args=get_connect_args(), **kwargs)


# SqlAlchemy models
class Base(DeclarativeBase):
    pass


class Restaurant(Base):
    __tablename__ = "restaurants"
    id = Column(Integer, Identity(start=1, cycle=True), primary_key=True)
    name = Column(String(100), nullable=False)
    address = Column(String(100), nullable=True)
