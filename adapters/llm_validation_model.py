from abc import ABC
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class SubAssignmentValidation(BaseModel):
    """Represents validation result for a single sub-assignment."""
    
    subassignment_id: str = Field(description="Unique identifier of the sub-assignment")
    validation_text: str = Field(description="Textual representation of model validation from validator")
    percentage: float = Field(description="Percentage of correctness (0 to 1) for the sub-assignment")


class LLMValidationModel(BaseModel, ABC):
    """Abstract base model for assignment validation."""
    
    student_name: str = Field(description="Name of the student")
    student_name_pairing_confidence: float = Field(description="Confidence score for the student name pairing (0 to 1)")
    validations: List[SubAssignmentValidation] = Field(
        default_factory=list,
        description="List of sub-assignment validations"
    )