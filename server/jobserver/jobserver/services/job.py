"""Job service. Service which handles all the requests on `job` resource."""
from typing import List, Set

from datetime import datetime

from starlette.requests import Request
from starlette.responses import JSONResponse

from jobserver.contexts import AppContext
from jobserver.core.service import Service
from jobserver.stores.job import JobStore
from jobserver.stores.user import UserStore


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
        applied_job_ids: Set[int] = user_store.get_user_job_ids(
            int(request.query_params["tenant"])
        )
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

    def update(self, request: Request) -> JSONResponse:
        """Only allow,
        1. Apply for job.
        2. Unapply for job.
        """
