
from pydantic import BaseModel, Field
from typing import Generic, TypeVar

from adapters.llm_validation_model import LLMValidationModel
from adapters.validation_metadata_model import ValidationMetadataModel


ModelType = TypeVar("ModelType", bound=LLMValidationModel)


class ValidationSummary(BaseModel, Generic[ModelType]):
    validation_metadata: ValidationMetadataModel = Field(description="Metadata about the validation process, including model used, final percentage, assignment file, timestamps, and temperature, filled programmatically from the validation process")
    llm_validation_response: ModelType = Field(description="Structured validation response from the LLM, including student name, pairing confidence, validation model, sub-assignment validations, final percentage, assignment file, timestamps, and temperature, filled programmatically from the validation process")
    filename: str = Field(description="Filename of the assignment")