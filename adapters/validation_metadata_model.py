from abc import ABC
from datetime import datetime
from typing import  Optional

from pydantic import BaseModel, Field


class ValidationMetadataModel(BaseModel, ABC):
    """Abstract base model for assignment metadata from validation."""
    validation_model: str = Field(description="Model used for validation")
    start_time: Optional[datetime] = Field(default=None, description="Start time of the validation")
    context_length: Optional[int] = Field(default=None, description="(Ollama specific) Context length used for validation, not supported for Gemini adapter")
    duration: Optional[float] = Field(default=None, description="Duration of the validation in milliseconds returned from LLM")
    end_time: Optional[datetime] = Field(default=None, description="End time of the validation")
    temperature: Optional[float] = Field(default=None, description="Temperature used for generation")
    prompt_tokens: Optional[int] = Field(default=None, description="Number of tokens in the input prompt")
    completion_tokens: Optional[int] = Field(default=None, description="Number of tokens generated in the output")
    total_duration: Optional[int] = Field(default=None, description="(Ollama specific) Total time spent generating the response, in nanoseconds")