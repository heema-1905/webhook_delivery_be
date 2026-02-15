from typing import Any, Optional

from fastapi.responses import JSONResponse


class CustomAPIResponse:
    """
    Response class defining the custom structure of success or error responses to be returned by the API endpoint
    """

    def get_success_response(
        self, code: int, message: str, data: Any = [], **kwargs
    ) -> dict:
        """
        This method creates a uniform success response for dict for successful API requests.
        """
        return {"code": code, "message": message, "data": data, **kwargs}

    def get_error_response(
        self,
        code: int,
        message: str,
        errors: Any = [],
        headers: Optional[dict] = None,
        **kwargs
    ):
        """
        This method creates a uniform JSON error response for failed API requests.
        """
        return JSONResponse(
            content={"code": code, "message": message, "errors": errors, **kwargs},
            status_code=code,
            headers=headers,
        )
