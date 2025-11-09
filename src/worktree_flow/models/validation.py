"""Validation models."""

from typing import Optional

from pydantic import BaseModel, Field


class ValidationError(BaseModel):
    """Validation error details."""

    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    fix_suggestion: Optional[str] = Field(None, description="Suggested fix")


class ValidationResult(BaseModel):
    """Validation result."""

    valid: bool = Field(..., description="Whether validation passed")
    errors: list[ValidationError] = Field(default_factory=list, description="Validation errors")
    warnings: list[str] = Field(default_factory=list, description="Warnings")
    checks_performed: list[str] = Field(default_factory=list, description="Checks performed")
