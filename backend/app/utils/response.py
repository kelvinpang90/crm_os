import decimal
import json
from typing import Any, Optional

from starlette.responses import Response


class _Encoder(json.JSONEncoder):
    def default(self, o: Any) -> Any:
        if isinstance(o, decimal.Decimal):
            return float(o)
        return super().default(o)


def _render(content: Any) -> bytes:
    return json.dumps(content, cls=_Encoder).encode("utf-8")


def ok(data: Any = None, message: str = "OK", status_code: int = 200) -> Response:
    body = _render({"success": True, "data": data, "message": message})
    return Response(content=body, status_code=status_code, media_type="application/json")


def fail(
    message: str,
    code: str = "ERROR",
    fields: Optional[dict] = None,
    status_code: int = 400,
) -> Response:
    body = _render({"success": False, "error": {"code": code, "message": message, "fields": fields}})
    return Response(content=body, status_code=status_code, media_type="application/json")
