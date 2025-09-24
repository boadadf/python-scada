import uuid
import datetime

def safe_serialize(obj):
    if isinstance(obj, uuid.UUID):
        return str(obj)
    if isinstance(obj, datetime.datetime):
        return obj.isoformat()
    return str(obj)  # fallback
