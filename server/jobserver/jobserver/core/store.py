"""Store skeletion which MUST be extended by all store implementations."""
from abc import ABC

from sqlalchemy.engine.base import Engine
from sqlalchemy import MetaData

from jobserver.contexts import DBConfig
from jobserver.db import create_engine_


class Store(ABC):
    """Store skeleton."""

    def __init__(self, db_config: DBConfig, table_metadata: MetaData) -> None:
        self._engine: Engine = create_engine_(
            db_config.host,
            db_config.port,
            db_config.username,
            db_config.password,
            db_config.db_name,
        ).execution_options(isolation_level="AUTOCOMMIT")
        self._table_metadata: MetaData = table_metadata
