"""Utils to initialize DB."""
from typing import List, Optional
from datetime import datetime, timezone

from sqlalchemy import MetaData, create_engine, text
from sqlalchemy.engine.base import Engine, Connection
from sqlalchemy.exc import DatabaseError, IntegrityError

from jobserver.utils import generate_id

_DEFAULT_POSTFRES_DB_NAME: str = "postgres"
_ID_TO_TENANT_ID_RSHIFT: int = 47


def create_engine_(
    host: str, port: int, username: str, password: str, db_name: str
) -> Engine:
    """Create a new connection to engine."""
    return create_engine(f"postgresql://{username}:{password}@{host}:{port}/{db_name}")


class InitDB:
    """DB initializer.

    * Create database in given name.
    * Create users with given ids.
    * Create row level policy for the users on tables where `id` doesnt have
      autoincrement.
    """

    def __init__(  # pylint: disable=too-many-arguments
        self,
        metadata: MetaData,
        db_name: str,
        host: str,
        port: int,
        username: str,
        password: str,
        tenant_ids: List[int],
    ) -> None:
        self._db_name: str = db_name
        self._host: str = host
        self._port: int = port
        self._username: str = username
        self._password: str = password
        self._metadata: MetaData = metadata
        self._tenant_ids: List[int] = tenant_ids

    def create_engine(self, db_name: Optional[str] = None) -> Engine:
        """Create a new engine with given configs.
        NOTE: Dispose engine once the use is over.
        """
        # Default database.
        if db_name is None:
            engine: Engine = create_engine_(
                self._host,
                self._port,
                self._username,
                self._password,
                _DEFAULT_POSTFRES_DB_NAME,
            )
        # Specified database, enter with super user previlege.
        else:
            engine = create_engine_(
                self._host, self._port, self._username, self._password, db_name
            )
        return engine

    def create_db(self) -> None:
        """Create all tables in the metadata.
        * Create database with given name.
        * Create all tables in db.
        """
        default_engine: Engine = self.create_engine().execution_options(
            isolation_level="AUTOCOMMIT"
        )
        # Transaction will be autocommited on exiting context-manager, if no error
        # is raised during any of the operation.
        with default_engine.connect() as conn:
            conn.execute(text(f"create database {self._db_name}"))
            curr_engine: Engine = self.create_engine(db_name=self._db_name)
            self._metadata.create_all(curr_engine)
            curr_engine.dispose()
        default_engine.dispose()

    def drop_db(self) -> None:
        """Drop database."""
        engine: Engine = self.create_engine().execution_options(
            isolation_level="AUTOCOMMIT"
        )
        with engine.connect() as conn:
            conn.execute(text(f"drop database {self._db_name}"))
        engine.dispose()

    def create_roles(self) -> None:
        """Create roles for all given tenants."""
        for tenant_id in self._tenant_ids:
            self.create_role(tenant_id)

    def create_role(self, tenant_id: int) -> str:
        """Create role and configs for tenant.
        * Create role in the <database>
        * Create the RLS policy for the role for all tables in <database>.
        """
        engine: Engine = self.create_engine(self._db_name)

        with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            role_name: str = f"tenant_{tenant_id}"
            # Create role.
            conn.execute(text(f"create role {role_name}"))
            for table_name in self._metadata.tables:
                # No need to create RLS policy for tables with autoincrement id.
                if (
                    self._metadata.tables[table_name].columns["id"].autoincrement
                    is True
                ):
                    continue
                # Enable row level security for table.
                conn.execute(
                    text(f"""alter table "{table_name}" enable row level security""")
                )
                # Grant privielges on table for the role.
                conn.execute(
                    text(
                        """grant all privileges on table """
                        + f""""{table_name}" to {role_name}"""
                    )
                )
                # Create RLS policy for the role on the table.
                conn.execute(
                    text(
                        f"""create policy "{table_name}.{role_name}" """
                        + f"""on "{table_name}" as permissive for all to {role_name} """
                        + f"""using (id >> {_ID_TO_TENANT_ID_RSHIFT} = {tenant_id})"""
                    )
                )
        engine.dispose()
        return role_name

    def drop_roles(self) -> None:
        """Drop all roles."""
        for tenant_id in self._tenant_ids:
            self.drop_role(tenant_id)

    def drop_role(self, tenant_id: int) -> None:
        """Drop the given role.
        NOTE: In psql role is not specific to db/schema it is global.
        """
        engine: Engine = self.create_engine().execution_options(
            isolation_level="AUTOCOMMIT"
        )
        with engine.connect() as conn:
            conn.execute(text(f"drop role tenant_{tenant_id}"))
        engine.dispose()


class InitData:
    """Initial data loader."""

    def __init__(
        self,
        users: List[dict],
        jobs: List[dict],
        db_name: str,
        host: str,
        port: int,
        username: str,
        password: str,
    ) -> None:
        self._users: List[dict] = users
        self._jobs: List[dict] = jobs
        self._engine: Engine = create_engine_(
            host, port, username, password, db_name
        ).execution_options(isolation_level="AUTOCOMMIT")

    def create_users(self) -> None:
        """Create provided users."""
        curr_time_milli: int = int(datetime.now(timezone.utc).timestamp() * 1000)

        with self._engine.connect() as conn:
            for user_obj in self._users:
                conn.execute(
                    text(
                        """INSERT INTO "User"(id, "createdTime", "lastModifiedTime", name, email)"""
                        + f"""VALUES ({generate_id(user_obj["id"])}, {curr_time_milli}, {curr_time_milli}, '{user_obj["name"]}', '{user_obj["email"]}')"""
                    )
                )

    def create_jobs(self) -> None:
        """Create provided jobs."""
        curr_time_milli: int = int(datetime.now(timezone.utc).timestamp() * 1000)

        with self._engine.connect() as conn:
            for job_obj in self._jobs:
                conn.execute(
                    text(
                        """INSERT INTO "Job"("createdTime", "lastModifiedTime", name, company, "expectedExperienceInYears", locations, "shortJobDescription", "shortCompanyDescription", "fullJobDescription")"""
                        + f"""VALUES ({curr_time_milli}, {curr_time_milli}, '{job_obj["name"]}', '{job_obj["company"]}', '{job_obj["expectedExperienceInYears"]}', '{job_obj["locations"]}', '{job_obj["shortJobDescription"]}', '{job_obj["shortCompanyDescription"]}', '{job_obj["fullJobDescription"]}')"""
                    )
                )


class DBSession:
    """Manage a db session."""

    def __init__(self, conn: Connection, tenant_id: int) -> None:
        self._conn: Connection = conn
        self._tenant_id: int = tenant_id

    def open(self) -> None:
        """Set schema and role"""
        self._conn.execute(text(f"set role tenant_{self._tenant_id}"))

    def close(self) -> None:
        """Reset schema and role"""
        self._conn.execute(text("reset role"))
