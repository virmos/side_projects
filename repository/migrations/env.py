from __future__ import annotations

import os
from logging.config import fileConfig

import sys
from pathlib import Path
from sqlalchemy import pool, create_engine
from sqlalchemy.engine import Connection

from alembic import context

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from models.db.database import Base  # type: ignore  # noqa: E402
from models.db import orders  # noqa: F401,E402 ensure models are imported


config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = os.environ.get("DATABASE_URL")
    if url and url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    url = os.environ.get("DATABASE_URL")
    if url and url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
    connectable = create_engine(url)

    with connectable.connect() as connection:  # type: ignore[arg-type]
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()


