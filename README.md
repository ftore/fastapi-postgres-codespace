
# FastAPI and Postgres Dev Environment with Codespadces

This repo can be opened in a [Codespaces](https://docs.github.com/en/codespaces/overview) - a development environment hosted in the cloud. You can open this repo in a [browser](https://docs.github.com/en/codespaces/developing-in-codespaces/creating-a-codespace-for-a-repository) or IDE like [VS Code](https://code.visualstudio.com/docs/remote/codespaces) with the [GitHub Codespaces extension](https://marketplace.visualstudio.com/items?itemName=GitHub.codespaces).

## Running the sample

1. Copy *.env.devcontainer* to *.env*. Set `DBSCHEMA` to the Postgres schema the
   tables should live in (defaults to `public`); it is created if missing.

2. Install dependencies and apply the database migrations:

  ```
  poetry install
  poetry run alembic upgrade head
  ```

3. Start the web app:

  ```
  poetry run uvicorn main:app --reload
  ```

## Running against the Databricks database

*.env-prod* points at the Lakebase endpoint and carries no password: with `ENV=prod`
the app fetches a 60-minute database token through the Databricks SDK and rotates it
before expiry. Locally it authenticates with the CLI profile named by
`DATABRICKS_CONFIG_PROFILE`; on Databricks Apps (*app.yml*) it uses the app's own
identity, and `PGHOST`/`PGPORT`/`PGUSER`/`PGDATABASE`/`PGSSLMODE` are injected by the
platform for the attached database resource.

  ```
  ENV_FILE=.env-prod poetry run uvicorn main:app --reload
  ```

## Database migrations

The schema is managed by [Alembic](https://alembic.sqlalchemy.org/). *alembic/env.py*
reads the same connection settings as the app from *db.py*, so no database URL is
stored in *alembic.ini*. After changing a model in *db.py*:

  ```
  poetry run alembic revision --autogenerate -m "describe the change"
  poetry run alembic upgrade head
  ```

## Pydantic and SQLAlchemy

[Pydantic](https://docs.pydantic.dev/latest/) is for data validation and settings managment using Python type annotations. [SQLAlchemy]() is a SQL toolkit and Object Relational Mapper (ORM).
