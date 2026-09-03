import os
import threading
from datetime import datetime, timedelta, timezone
from urllib.parse import quote_plus

from dotenv import load_dotenv
from sqlalchemy import Column, Identity, Integer, String, create_engine, event
from sqlalchemy.orm import DeclarativeBase

# Which env file to load; override with ENV_FILE=.env-prod to run locally
# against the Databricks-hosted database.
ENV_FILE = os.environ.get("ENV_FILE", ".env")
load_dotenv(ENV_FILE)

ENV = os.environ.get("ENV", "dev")

# libpq-style connection settings. Databricks Apps injects PGHOST/PGPORT/PGUSER/
# PGDATABASE/PGSSLMODE automatically for an attached Lakebase database resource,
# so in prod these come from the platform rather than from a file.
PGHOST = os.environ["PGHOST"]
PGPORT = os.environ.get("PGPORT", "5432")
PGUSER = os.environ["PGUSER"]
PGDATABASE = os.environ["PGDATABASE"]
PGSSLMODE = os.environ.get("PGSSLMODE", "disable")
# Static password for local Postgres. Unset in prod, where the password is a
# short-lived Databricks token fetched by get_token_password().
PGPASS = os.environ.get("PGPASS")
# Postgres schema the tables live in; defaults to the standard "public"
DBSCHEMA = os.environ.get("DBSCHEMA", "public")

# Lakebase endpoints follow the structure: projects/<id>/branches/<id>/endpoints/<id>
LAKEBASE_ENDPOINT_NAME = os.environ.get("LAKEBASE_ENDPOINT_NAME")

USE_DATABRICKS_TOKEN = ENV == "prod"

# Databricks database tokens are valid for 60 minutes. Refresh with margin to
# spare so a connection is never opened with a credential about to expire.
TOKEN_LIFETIME = timedelta(minutes=60)
TOKEN_REFRESH_MARGIN = timedelta(minutes=10)

_token_lock = threading.Lock()
_token: str | None = None
_token_expires_at: datetime = datetime.min.replace(tzinfo=timezone.utc)


def _to_datetime(expires_at) -> datetime:
    """Normalizes the SDK's expiry (protobuf Timestamp, datetime, or str)."""
    if expires_at is None:
        return datetime.now(timezone.utc) + TOKEN_LIFETIME
    if hasattr(expires_at, "seconds"):  # google.protobuf.Timestamp
        return datetime.fromtimestamp(expires_at.seconds, tz=timezone.utc)
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    return expires_at


def _generate_databricks_credential() -> tuple[str, datetime]:
    """Requests a fresh database credential from Databricks."""
    from databricks.sdk import WorkspaceClient

    if not LAKEBASE_ENDPOINT_NAME:
        raise RuntimeError(
            "ENV=prod requires LAKEBASE_ENDPOINT_NAME, e.g. "
            "projects/<id>/branches/<id>/endpoints/<id>"
        )

    w = WorkspaceClient()
    creds = w.postgres.generate_database_credential(endpoint=LAKEBASE_ENDPOINT_NAME)
    return creds.token, _to_datetime(creds.expire_time)


def get_token_password() -> str:
    """Returns the database password, rotating the token before it expires."""
    if not USE_DATABRICKS_TOKEN:
        if PGPASS is None:
            raise RuntimeError(f"PGPASS is not set in {ENV_FILE}")
        return PGPASS

    global _token, _token_expires_at
    with _token_lock:
        if _token is None or datetime.now(timezone.utc) >= (
            _token_expires_at - TOKEN_REFRESH_MARGIN
        ):
            _token, _token_expires_at = _generate_databricks_credential()
        return _token


def get_database_uri() -> str:
    # The password is deliberately left out of the URL: in prod it rotates, so
    # it is supplied per-connection by the "do_connect" hook below.
    return (
        f"postgresql://{quote_plus(PGUSER)}@{PGHOST}:{PGPORT}/{quote_plus(PGDATABASE)}"
    )


def get_connect_args() -> dict:
    # Point search_path at DBSCHEMA so unqualified table names resolve there.
    # This keeps the models and the migrations free of a hard-coded schema name.
    return {"options": f"-csearch_path={DBSCHEMA}", "sslmode": PGSSLMODE}


def create_db_engine(**kwargs):
    kwargs.setdefault("pool_pre_ping", True)
    if USE_DATABRICKS_TOKEN:
        # Retire pooled connections well inside the token lifetime.
        kwargs.setdefault("pool_recycle", int(TOKEN_LIFETIME.total_seconds()) - 900)

    engine = create_engine(
        get_database_uri(), connect_args=get_connect_args(), **kwargs
    )

    @event.listens_for(engine, "do_connect")
    def _supply_password(dialect, conn_rec, cargs, cparams):
        # Runs for every new pooled connection, so each one gets a live token.
        cparams["password"] = get_token_password()

    return engine


# SqlAlchemy models
class Base(DeclarativeBase):
    pass


class Restaurant(Base):
    __tablename__ = "restaurants"
    id = Column(Integer, Identity(start=1, cycle=True), primary_key=True)
    name = Column(String(100), nullable=False)
    address = Column(String(100), nullable=True)
