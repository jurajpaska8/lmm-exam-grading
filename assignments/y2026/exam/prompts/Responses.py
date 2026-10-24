from abc import ABC
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class SubAssignmentValidation_exam2026_v1(BaseModel):
    """Represents validation result for a single sub-assignment."""
    
    subassignment_id: str = Field(description="Unique identifier of the sub-assignment")
    extracted_text: str = Field(description="Textual representation of extracted text from assignment")
    validation_text: str = Field(description="Textual representation of model validation from validator")
    percentage: float = Field(description="Percentage of correctness (0 to 1) for the sub-assignment")


class LLMValidationModel_exam2026_v1(BaseModel, ABC):
    """Abstract base model for assignment validation."""
    
    validations: List[SubAssignmentValidation_exam2026_v1] = Field(
        default_factory=list,
        description="List of sub-assignment validations"
    )