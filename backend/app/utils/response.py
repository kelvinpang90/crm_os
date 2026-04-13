from typing import Any, Optional
from fastapi.responses import JSONResponse


def ok(data: Any = None, message: str = "操作成功", status_code: int = 200) -> JSONResponse:
    return JSONResponse(
        content={"success": True, "data": data, "message": message},
        status_code=status_code,
    )


def fail(
    message: str,
    code: str = "ERROR",
    fields: Optional[dict] = None,
    status_code: int = 400,
) -> JSONResponse:
    return JSONResponse(
        content={
            "success": False,
            "error": {"code": code, "message": message, "fields": fields},
        },
        status_code=status_code,
    )
