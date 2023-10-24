"""Job service. Service which handles all the requests on `job` resource."""
from typing import List, Set, Union
from http import HTTPStatus
from dataclasses import asdict

from datetime import datetime

from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from sqlalchemy.exc import DataError, IntegrityError

from jobserver.contexts import AppContext
from jobserver.core.service import Service
from jobserver.stores.job import JobStore
from jobserver.stores.user import UserStore
from jobserver.errors import INVALID_ID, INVALID_TENANT_ID, REL_ALREADY_EXISTS


class JobService(Service):
    """Handle all the actons on job."""

    def __init__(self, app_context: AppContext) -> None:
        super().__init__(app_context)

    def fetch_all(self, request: Request) -> JSONResponse:
        """Fetch all jobs.
        Mark it as applied if user-job mapping is there.
        """
        job_store: JobStore = JobStore(
            self._app_context.db_config, self._app_context.table_metadata
        )
        user_store: UserStore = UserStore(
            self._app_context.db_config, self._app_context.table_metadata
        )
        jobs: List[dict] = job_store.get_all()
        try:
            applied_job_ids: Set[int] = user_store.get_user_job_ids(
                int(request.query_params["tenant"])
            )
        except DataError as exc:
            # Invalid tenant id value.
            if exc.orig.pgcode == "22023":
                return JSONResponse(
                    asdict(INVALID_TENANT_ID), status_code=int(INVALID_TENANT_ID.status)
                )
            raise exc
        result: List[dict] = []
        for job_obj in jobs:
            result.append(
                {
                    "id": job_obj["id"],
                    "name": job_obj["name"],
                    "company": job_obj["company"],
                    "expectedExperienceInYears": job_obj["expectedExperienceInYears"],
                    "locations": job_obj["locations"],
                    "createdTime": str(
                        datetime.utcfromtimestamp(
                            (job_obj["createdTime"] / 1000)
                        ).strftime("%Y-%m-%dT%H:%M:%SZ")
                    ),
                    "shortJobDescription": job_obj["shortJobDescription"],
                    "shortCompanyDescription": job_obj["shortCompanyDescription"],
                    "fullJobDescription": job_obj["fullJobDescription"],
                    "isApplied": job_obj["id"] in applied_job_ids,
                }
            )
        return JSONResponse(result)

    async def update(self, request: Request) -> Union[Response, JSONResponse]:
        """Only allow,
        1. Apply for job.
        2. Unapply for job.
        """
        body: dict = await request.json()
        user_store: UserStore = UserStore(
            self._app_context.db_config, self._app_context.table_metadata
        )
        tenant_id: int = int(request.query_params["tenant"])
        job_id: int = int(request.path_params["job_id"])

        try:
            if body["isApplied"] is True:
                try:
                    user_store.create_user_job_relation(tenant_id, job_id)
                except IntegrityError as exc:
                    # Violation of unique constraint
                    if exc.orig.pgcode == "23505":
                        return JSONResponse(
                            asdict(REL_ALREADY_EXISTS),
                            status_code=int(REL_ALREADY_EXISTS.status),
                        )
                    # Non existing foreign key error
                    if exc.orig.pgcode == "23503":
                        return JSONResponse(
                            asdict(INVALID_ID), status_code=int(INVALID_ID.status)
                        )
                    raise exc
            else:
                if user_store.remove_user_job_relation(tenant_id, job_id) is False:
                    return JSONResponse(
                        asdict(INVALID_ID), status_code=int(INVALID_ID.status)
                    )
        except DataError as exc:
            # Invalid tenant id value.
            if exc.orig.pgcode == "22023":
                return JSONResponse(
                    asdict(INVALID_TENANT_ID), status_code=int(INVALID_TENANT_ID.status)
                )
            raise exc
        return Response(status_code=HTTPStatus.NO_CONTENT)
