from typing import Any, List

from pydantic import BaseModel, Field


class HealthCheck(BaseModel):
    """
    Schema class defining the health check endpoint response fields
    """

    status: str


class BaseResponseSchema(BaseModel):
    """
    Schema class defining the generic base response fields that are common to all API endpoint responses
    """

    code: int
    message: str
    data: Any = []


class BasePaginatedResponseSchema(BaseModel):
    """
    Base response schema for getting paginated response.
    """

    total_count: int
    results: List[Any]


class BaseAggregateSchema(BaseModel):
    """Schema representing an aggregate count with ID."""

    id: Any = Field(..., alias="_id")
    count: int
