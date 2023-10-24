"""Handle database activities for `job` resource."""
from typing import List

from sqlalchemy import MetaData, select

from jobserver.contexts import DBConfig
from jobserver.core.store import Store


class JobStore(Store):
    """Database activities related to job resource."""

    def __init__(self, db_config: DBConfig, table_metadata: MetaData) -> None:
        super().__init__(db_config, table_metadata)

    def get_all(self) -> List[dict]:
        """Get all jobs."""
        stmt = select(self._table_metadata.tables["Job"])
        jobs: List[dict] = []

        with self._engine.connect() as conn:
            for row in conn.execute(stmt):
                jobs.append(row._asdict())
        return jobs
