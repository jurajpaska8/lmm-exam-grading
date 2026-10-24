from adapters.LLMAdapter import LLMAdapter, ResponseType
from typing import Type
from PIL.Image import Image

from adapters.validation_response_model import ValidationResponseModel


class GenericAgent:
    """ This is a generic agent that can be used for various tasks. 
    It uses an LLM to process the input and generate a response. 
    The specific task and response format can be defined by the user through the prompts and response models. 
    IMPROVEMENT: provide prompt template and dictionary of variables to fill the prompt template as arguments 
    """
    def __init__(self, llm_adapter: LLMAdapter):
        self.llm_adapter = llm_adapter
    
    def identify_student(self, scanned_image: Image, user_prompt: str, temperature: float, context_length: int, llm_model: str, response_model: Type[ResponseType]) -> ValidationResponseModel[ResponseType]:
        # print(f"{self.__class__.__name__}: processing image ")

        response = self.llm_adapter.generate_response(
            model=llm_model,
            system_prompt="", 
            user_prompt=user_prompt,
            temperature=temperature,
            images=[scanned_image], 
            context_length=context_length, 
            response_model=response_model)
        # print(f"{self.__class__.__name__}: inference completed")
        return response
    
