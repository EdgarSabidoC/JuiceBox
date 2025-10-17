from typing import Any
from pydantic import BaseModel


class Response(BaseModel):
    status: str
    message: str
    data: dict[str, Any] = {}

    @classmethod
    def ok(cls, message="Success", data=None):
        return cls(status="OK", message=message, data=data or {})

    @classmethod
    def error(cls, message="Something went wrong", data=None):
        return cls(status="ERROR", message=message, data=data or {})
