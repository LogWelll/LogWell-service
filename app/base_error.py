from fastapi import HTTPException, status


class BaseError:
    error: HTTPException
    example: dict

    def __init__(self, status_code: int, detail: str):
        self.error = HTTPException(status_code=status_code, detail=detail)
        self.example = {"detail": detail}


class NotFoundError(BaseError):
    def __init__(self, resource: str = "Logs"):
        detail = f"{resource} not found"
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)

        self.example = {
            "detail": detail,
        }
