from base_error import BaseError
from fastapi import status


class ServiceUnavailableError(BaseError):
    def __init__(self, detail: str = "Message queue is not available."):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail,
        )

        self.example = {
            "detail": detail,
        }
