from ....core.operations import APIOperation
from .schemas import UsageEventsResponse, UsageSummaryResponse

_GET_LANDSCAPE_SUMMARY_OP = APIOperation(
    method="GET",
    endpoint_template="/usage/teams/{team_id}/resources/landscape-service/summary",
    response_model=UsageSummaryResponse,
)

_GET_LANDSCAPE_EVENTS_OP = APIOperation(
    method="GET",
    endpoint_template="/usage/teams/{team_id}/resources/landscape-service/{resource_id}/events",
    response_model=UsageEventsResponse,
)
