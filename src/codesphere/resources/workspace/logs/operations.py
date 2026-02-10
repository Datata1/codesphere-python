from ....core.operations import StreamOperation
from .schemas import LogEntry

_STREAM_STAGE_LOGS_OP = StreamOperation(
    endpoint_template="/workspaces/{id}/logs/{stage}/{step}",
    entry_model=LogEntry,
)

_STREAM_SERVER_LOGS_OP = StreamOperation(
    endpoint_template="/workspaces/{id}/logs/run/{step}/server/{server}",
    entry_model=LogEntry,
)

_STREAM_REPLICA_LOGS_OP = StreamOperation(
    endpoint_template="/workspaces/{id}/logs/run/{step}/replica/{replica}",
    entry_model=LogEntry,
)
