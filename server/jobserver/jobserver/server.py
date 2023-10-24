"""Server running module."""
from typing import Final

from starlette.applications import Starlette
from starlette.routing import Route, Mount

from jobserver.contexts import AppContext, DBConfig
from jobserver.env_util import Config

# NOTE: If there are huge no. of services in future, need a different way to
#       register services. Something dynamic.
from jobserver.services.job import JobService
from jobserver.contract.models import METADATA

_ENV_CONFIGS: Final = Config(".env")
_APP_CONTEXT: AppContext = AppContext(
    db_config=DBConfig(
        db_name=_ENV_CONFIGS.get("DB_NAME"),
        host=_ENV_CONFIGS.get("DB_HOST"),
        port=int(_ENV_CONFIGS.get("DB_PORT")),
        username=_ENV_CONFIGS.get("DB_USERNAME"),
        password=_ENV_CONFIGS.get("DB_PASSWORD"),
    ),
    table_metadata=METADATA,
    debug=bool(_ENV_CONFIGS.get("DEBUG", default=None)),
)

app = Starlette(
    debug=_APP_CONTEXT.debug,
    routes=[
        Mount(
            "/jobs",
            routes=[
                Route("/", JobService(_APP_CONTEXT).fetch_all, methods=["GET"]),
                Route("/{job_id}", JobService(_APP_CONTEXT).update, methods=["PATCH"]),
            ],
        )
    ],
    # The below options are not using for now, may needed in the future.
    middleware=None,
    on_startup=None,
    on_shutdown=None,
)
