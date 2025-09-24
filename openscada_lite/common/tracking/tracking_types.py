from enum import Enum

class DataFlowStatus(Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    RECEIVED = "received"
    BLOCKED = "blocked"
    FORWARDED = "forwarded"
    CREATED = "created"