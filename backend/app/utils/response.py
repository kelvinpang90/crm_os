import datetime
import decimal
import json
from typing import Any, Optional

from starlette.responses import Response

from app.utils.utc import mark_utc


class _Encoder(json.JSONEncoder):
    def default(self, o: Any) -> Any:
        if isinstance(o, decimal.Decimal):
            return float(o)
        # A raw datetime used to be a 500 here, which is why every service
        # stringifies its own before handing the payload over. Handling it means
        # a new one can be passed straight through and still lands marked --
        # `datetime` tested before `date`, because it is a subclass of it.
        if isinstance(o, datetime.datetime):
            return mark_utc(o.isoformat())
        if isinstance(o, datetime.date):
            return o.isoformat()
        return super().default(o)


def _render(content: Any) -> bytes:
    # The single point every response passes through. Timestamps here are naive
    # UTC, and a browser reads an offset-less one as local time -- which is how
    # a card created at 16:49 came to read 08:49. See `app/utils/utc.py`.
    return json.dumps(mark_utc(content), cls=_Encoder).encode("utf-8")


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
