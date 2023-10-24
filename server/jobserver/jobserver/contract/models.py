"""Table definitions."""
from sqlalchemy import (
    Table,
    Column,
    String,
    MetaData,
    BigInteger,
    ForeignKey,
    UniqueConstraint,
)

METADATA = MetaData()

User = Table(
    "User",
    METADATA,
    Column("id", BigInteger, primary_key=True, autoincrement=False),
    Column("createdTime", BigInteger, nullable=False),
    Column("lastModifiedTime", BigInteger, nullable=False),
    Column("name", String(500), nullable=False),
    Column("email", String(320), nullable=False),
    UniqueConstraint("email"),
    # NOTE: Additional columns needs to be added in future.
)

Job = Table(
    "Job",
    METADATA,
    # Autoincrement id is enabled, since this is a global level table and there
    # wont be any row level security to restrict user based access. Content of this
    # table needs to be added/modified using internal api.
    Column("id", BigInteger, primary_key=True, autoincrement=True),
    Column("createdTime", BigInteger, nullable=False),
    Column("lastModifiedTime", BigInteger, nullable=False),
    Column("name", String(500), nullable=False),
    # Currently company name is added as a string. In future if there are much more
    # requirements to get company's details, then this should be a FK to Company table.
    Column("company", String(500), nullable=False),
    Column("expectedExperienceInYears", String(10), nullable=True),
    Column("locations", String(500), nullable=True),
    Column("shortJobDescription", String(1000), nullable=True),
    Column("shortCompanyDescription", String(1000), nullable=True),
    Column("fullJobDescription", String(10000), nullable=False),
)

UserJob = Table(
    "UserJob",
    METADATA,
    Column("id", BigInteger, primary_key=True, autoincrement=False),
    Column(
        "userID", BigInteger, ForeignKey("User.id", ondelete="CASCADE"), nullable=False
    ),
    Column(
        "jobID", BigInteger, ForeignKey("Job.id", ondelete="CASCADE"), nullable=False
    ),
    UniqueConstraint("userID", "jobID"),
)
