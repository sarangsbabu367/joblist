"""Handle user related store apis."""
from typing import Set

from sqlalchemy import MetaData, select, insert, delete, func

from jobserver.contexts import DBConfig
from jobserver.core.store import Store
from jobserver.db import DBSession
from jobserver.utils import generate_id


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
                job_ids = job_ids.union(row[0])
            db_session.close()
        return job_ids

    def get_user_id(self, tenant_id: int) -> int:
        """Get user-id of the tenant."""
        table = self._table_metadata.tables["User"]
        stmt = select(table.c.id)

        with self._engine.connect() as conn:
            db_session: DBSession = DBSession(conn, tenant_id)
            db_session.open()
            user_id: int = conn.execute(stmt).fetchone()[0]
            db_session.close()
        return user_id

    def create_user_job_relation(self, tenant_id: int, job_id: int) -> None:
        """Create user - job relation."""
        table = self._table_metadata.tables["UserJob"]
        stmt = insert(table).values(
            id=generate_id(tenant_id), userID=self.get_user_id(tenant_id), jobID=job_id
        )

        with self._engine.connect() as conn:
            db_session: DBSession = DBSession(conn, tenant_id)
            db_session.open()
            conn.execute(stmt)
            db_session.close()

    def remove_user_job_relation(self, tenant_id: int, job_id: int) -> None:
        """Remove the given user - job relation."""
        table = self._table_metadata.tables["UserJob"]
        stmt = delete(table).where(table.c.jobID == job_id).returning(table.c.id)
        record_exists: bool = False

        with self._engine.connect() as conn:
            db_session: DBSession = DBSession(conn, tenant_id)
            db_session.open()
            for row in conn.execute(stmt):
                record_exists = True
                break

            db_session.close()
        return record_exists
