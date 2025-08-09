from base_response import BaseResponse
from logs.schemas import LogRetrieveSchema


def create_log_response(record: LogRetrieveSchema):
    return BaseResponse[LogRetrieveSchema](
        message="Log added successfully",
        data=record,
    )


def read_log_response(record: LogRetrieveSchema):
    return BaseResponse[LogRetrieveSchema](
        message="Log retrieved successfully",
        data=record,
    )


def read_logs_response(records: list[LogRetrieveSchema]):
    return BaseResponse[list[LogRetrieveSchema]](
        message="Logs retrieved successfully",
        data=records,
    )

def non_blocking_create_log_response(record: dict):
    return BaseResponse[dict](
        message="Log creation queued successfully",
        data=record,
    )