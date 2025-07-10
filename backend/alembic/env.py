print("!!!!!!!!!! EXECUTING backend/alembic/env.py NOW !!!!!!!!!!") # Obvious print

from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool
from sqlalchemy import create_engine

from alembic import context

import sys
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

print(f"sys.path in env.py: {sys.path}")
# Accessing context.config.attributes here for -x test
try:
    custom_arg = context.config.attributes.get('my_custom_arg')
    print(f"Custom argument from -x: my_custom_arg = {custom_arg}")
except Exception as e:
    print(f"Could not access context.config.attributes: {e}")


try:
    from backend.app.models import Base # Import Base
    print("Successfully imported Base from backend.app.models")
    print(f"Tables in Base.metadata at import time: {list(Base.metadata.tables.keys())}")
except ImportError as e:
    print(f"ERROR importing Base: {e}")
    raise

try:
    from backend.core.config import settings # Import settings
    print("Successfully imported settings from backend.core.config")
except ImportError as e:
    print(f"ERROR importing settings: {e}")
    raise


config = context.config # This is the main config object from alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = settings.DATABASE_URL
    print(f"OFFLINE: About to configure context. Tables in Base.metadata: {list(Base.metadata.tables.keys())}")
    context.configure(
        url=url,
        target_metadata=Base.metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    ini_section = config.get_section(config.config_ini_section, {})
    ini_section['sqlalchemy.url'] = settings.DATABASE_URL
    connectable = engine_from_config(
        ini_section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        print(f"ONLINE: About to configure context. Tables in Base.metadata: {list(Base.metadata.tables.keys())}")
        context.configure(
            connection=connection,
            target_metadata=Base.metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    print("Running migrations OFFLINE")
    run_migrations_offline()
else:
    print("Running migrations ONLINE")
    run_migrations_online()

print("!!!!!!!!!! FINISHED EXECUTING backend/alembic/env.py !!!!!!!!!!")
