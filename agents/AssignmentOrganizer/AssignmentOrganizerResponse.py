from typing import Generic, TypeVar
from pydantic import BaseModel, Field
from adapters.LLMAdapter import ResponseType

class AssignmentOrganizerResponseV1(BaseModel, Generic[ResponseType]):
    student_name: str = Field(description="The name of the student associated with the scanned assignment images, extracted from the images using the LLM.")
    student_idx: int = Field(description="The index of the student associated with the scanned assignment images.")
    confidence_score: float = Field(description="A confidence score between 0 and 1 indicating the LLM's confidence in the association between the student name and the scanned assignment images, based on the analysis of the images.")
    is_blank_name: bool = Field(description="Indicates whether the extracted student name is blank.")
    is_illegible_name: bool = Field(description="Indicates whether the extracted student name is illegible.")
