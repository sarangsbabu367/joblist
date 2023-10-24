"""Errors."""
from dataclasses import dataclass
from http import HTTPStatus


@dataclass(frozen=True)
class Error:
    status: str
    code: str
    title: str
    detail: str


INVALID_TENANT_ID = Error(
    status=str(HTTPStatus.BAD_REQUEST.value),
    code="1",
    title="Invalid tenant id",
    detail="The given tenant-id doesn't exists in the system.",
)
REL_ALREADY_EXISTS = Error(
    status=str(HTTPStatus.BAD_REQUEST.value),
    code="2",
    title="Relation exists",
    detail="The given relation already exists in the system.",
)
INVALID_ID = Error(
    status=str(HTTPStatus.NOT_FOUND.value),
    code="3",
    title="Invalid id value",
    detail="Given id does not exists.",
)
