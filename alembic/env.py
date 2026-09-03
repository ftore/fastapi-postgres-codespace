from logging.config import fileConfig

from sqlalchemy import pool, text

from alembic import context
from db import DBSCHEMA, Base, create_db_engine, get_database_uri

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Model metadata, for 'autogenerate' support
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    context.configure(
        url=get_database_uri(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.execute(f'SET search_path TO "{DBSCHEMA}"')
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = create_db_engine(poolclass=pool.NullPool)

    with connectable.connect() as connection:
        # The engine's search_path points at DBSCHEMA, so the schema has to
        # exist before any migration (or the alembic_version table) is written.
        connection.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{DBSCHEMA}"'))
        connection.commit()

        # No version_table_schema here: search_path already makes DBSCHEMA the
        # default schema, so alembic_version is created there too.
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
