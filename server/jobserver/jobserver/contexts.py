"""Context implementations."""
from dataclasses import dataclass
from collections import namedtuple

from sqlalchemy import MetaData

DBConfig = namedtuple("DBConfig", "db_name host port username password")


@dataclass(frozen=True)
class AppContext:
    """Top level context for application."""

    db_config: DBConfig
    table_metadata: MetaData
    debug: bool
