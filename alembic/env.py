from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
from app.db.base import Base
from app.db.models import *  # noqa: F401, F403
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def get_url():
    """从环境变量或配置文件获取数据库 URL"""
    from app.core.config import get_settings
    settings = get_settings()
    if not settings.database_url:
        raise ValueError("DATABASE_URL 未配置，请在 .env 文件中设置")
    return settings.database_url


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = get_url()
    # 将异步 URL 转换为同步 URL
    if url.startswith("mysql+aiomysql://"):
        url = url.replace("mysql+aiomysql://", "mysql+pymysql://")
    elif url.startswith("sqlite+aiosqlite://"):
        url = url.replace("sqlite+aiosqlite://", "sqlite://")
    
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # 从配置获取数据库 URL
    configuration = config.get_section(config.config_ini_section, {})
    database_url = get_url()
    
    # 将异步 URL 转换为同步 URL（Alembic 需要同步连接）
    # mysql+aiomysql:// -> mysql+pymysql://
    # sqlite+aiosqlite:// -> sqlite://
    if database_url.startswith("mysql+aiomysql://"):
        database_url = database_url.replace("mysql+aiomysql://", "mysql+pymysql://")
    elif database_url.startswith("sqlite+aiosqlite://"):
        database_url = database_url.replace("sqlite+aiosqlite://", "sqlite://")
    
    configuration["sqlalchemy.url"] = database_url
    
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

