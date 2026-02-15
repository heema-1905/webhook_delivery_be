from typing import Any, List, Optional

from fastapi import Query

from app.config.settings import settings


class PaginationParams:
    """
    Handles pagination parameters for FastAPI endpoints.

    Attributes:
        page (Optional[int]): The current page number from the query parameter.
        page_size (int): Number of items per page, pulled from settings.
        total_count (Optional[int]): Total number of items (to be set externally).
    """

    def __init__(
        self,
        page: Optional[int] = Query(None, gt=0, description="Page number"),
        page_size: Optional[int] = Query(
            None, gt=0, description="Limit of records to be retrieved in page"
        ),
    ):
        self.page = page or settings.DEFAULT_PAGE
        self.page_size = page_size or settings.PAGE_SIZE
        self.total_count = None

    @property
    def offset(self):
        """
        Computes the offset for pagination queries.

        Returns:
            Optional[int]: The number of records to skip based on the page.
        """
        if self.page and self.page_size:
            return (self.page - 1) * self.page_size
        return None

    def get_paginated_response_dict(
        self,
        results: List[Any],
        **kwargs,
    ) -> dict:
        """
        Formats the paginated response.

        Args:
            results (List[Any]): The list of results for the current page.

        Returns:
            dict: A dictionary containing pagination metadata and results.
        """
        return {
            "total_count": self.total_count,
            "results": results,
            **kwargs,
        }
