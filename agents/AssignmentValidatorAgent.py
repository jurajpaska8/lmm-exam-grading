from adapters.LLMAdapter import LLMAdapter, ResponseType
from adapters.llm_validation_model import LLMValidationModel
from adapters.validation_response_model import ValidationResponseModel
from helpers.prompt_builder import load_prompt_template, fill_prompt_template
from typing import List, Type, TypeVar
from pydantic import BaseModel
from PIL.Image import Image

class AssignmentValidatorAgent:
    def __init__(self, llm_adapter: LLMAdapter, prompt_path: str):
        self.llm_adapter = llm_adapter
        self.prompt_template = load_prompt_template(prompt_path)
    
    def process(self, images: List[Image], student_names: str, supervisor_feedback: str = None, previous_review: str = None, temperature: float = None, context_length: int = None, model: str = None, response_model: Type[ResponseType] = None) -> ValidationResponseModel[ResponseType]:
        print(f"{self.__class__.__name__}: processing {len(images)} images...")
        
        # Fill the prompt
        prompt = fill_prompt_template(self.prompt_template, {
            "STUDENT_NAMES": student_names
        })
        print(f"{self.__class__.__name__}: system prompt created with student_names")
        
        user_prompt = prompt
        if supervisor_feedback and previous_review:
            user_prompt += f"\n\n--- PREVIOUS REVIEW ---\n{previous_review}\n\n--- SUPERVISOR FEEDBACK ---\n{supervisor_feedback}\n\nPlease revise your review based on the Supervisor's feedback."
            print(f"{self.__class__.__name__}: refining based on supervisor feedback.")

        effective_response_model = response_model or LLMValidationModel
        print(f"{self.__class__.__name__}: running inference through LLMAdapter with model={model} response_model={effective_response_model.__name__}...")
        response = self.llm_adapter.generate_response(
            model=model,
            system_prompt="",
            user_prompt=user_prompt,
            images=images,
            temperature=temperature,
            context_length=context_length,
            response_model=effective_response_model

        )
        print(f"{self.__class__.__name__}: inference completed")
        return response
