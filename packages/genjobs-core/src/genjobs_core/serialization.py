"""Safe JSON-boundary validation for portable jobs."""

from __future__ import annotations

import json

from .models import JobRequest


def request_size_bytes(request: JobRequest) -> int:
    """Validate the portable portion of a request and return its UTF-8 size."""
    document = {
        "task": request.task,
        "payload": request.payload,
        "inputs": [
            {
                "location": item.location,
                "kind": item.kind.value,
                "media_type": item.media_type,
                "metadata": item.metadata,
            }
            for item in request.inputs
        ],
    }
    try:
        encoded = json.dumps(document, allow_nan=False, separators=(",", ":"), ensure_ascii=False)
    except (TypeError, ValueError) as error:
        raise ValueError("job payload and input metadata must be JSON serializable") from error
    return len(encoded.encode("utf-8"))
