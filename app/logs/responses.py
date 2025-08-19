from base_response import BaseResponse
from logs.schemas import LogRetrieveSchema


class LogCreateResponse(BaseResponse):
    def __init__(
        self,
        data: LogRetrieveSchema,
        message: str = "Log added successfully",
    ):
        super().__init__(message=message, data=data)


class LogReadResponse(BaseResponse):
    def __init__(
        self,
        data: LogRetrieveSchema,
        message: str = "Log retrieved successfully",
    ):
        super().__init__(message=message, data=data)


class LogReadListResponse(BaseResponse):
    total: int

    def __init__(
        self,
        data: list[LogRetrieveSchema],
        message: str = "Logs retrieved successfully",
        total: int = 0,
    ):
        super().__init__(message=message, data=data, total=total)
        self.total = total


class NonBlockingLogCreateResponse(BaseResponse):
    def __init__(
        self,
        data: dict,
        message: str = "Log creation queued successfully",
    ):
        super().__init__(message=message, data=data)
