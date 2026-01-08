from datetime import datetime
from fastapi.responses import JSONResponse
from openscada_lite.common.models.dtos import StatusDTO


def make_response(
    *,
    status: str,
    reason: str,
    status_code: int,
    data: dict | None = None,
    user: str | None = None,
    endpoint: str | None = None,
) -> JSONResponse:
    meta = {
        "status": status,
        "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
    }
    if user is not None:
        meta["user"] = user
    if endpoint is not None:
        meta["endpoint"] = endpoint

    payload = {}
    if data:
        payload.update(data)
    # Ensure meta is present under data; do not duplicate at root
    payload.update(meta)

    dto = StatusDTO(status=status, reason=reason, data=payload)
    return JSONResponse(status_code=status_code, content=dto.to_dict())
