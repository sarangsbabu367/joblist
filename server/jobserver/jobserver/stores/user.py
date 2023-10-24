"""Handle user related store apis."""
from typing import Set

from sqlalchemy import MetaData, select, func
from sqlalchemy.engine.base import Engine, RootTransaction

from jobserver.contexts import DBConfig
from jobserver.core.store import Store
from jobserver.db import DBSession


class UserStore(Store):
    """Database activities related to user resource."""

    def __init__(self, db_config: DBConfig, table_metadata: MetaData) -> None:
        super().__init__(db_config, table_metadata)

    def get_user_job_ids(self, tenant_id: int) -> Set[int]:
        """Get all job ids for which user has applied."""
        table = self._table_metadata.tables["UserJob"]
        stmt = select(func.array_agg(table.c.jobID))
        job_ids: Set[int] = set()

        with self._engine.connect() as conn:
            db_session: DBSession = DBSession(conn, tenant_id)
            db_session.open()
            for row in conn.execute(stmt):
                job_ids.add(*row)
            db_session.close()
        return job_ids
