"""Service skeletion which MUST be extended by all service implementations."""
from abc import ABC, abstractmethod

from starlette.requests import Request
from starlette.responses import JSONResponse

from jobserver.contexts import AppContext


class Service(ABC):
    """Service skeleton."""

    def __init__(self, app_context: AppContext) -> None:
        self._app_context: AppContext = app_context

    @abstractmethod
    def fetch_all(self, request: Request) -> JSONResponse:
        ...

    @abstractmethod
    def update(self, request: Request) -> JSONResponse:
        ...
