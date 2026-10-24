from datetime import datetime
from adapters.validation_metadata_model import ValidationMetadataModel
from adapters.llm_validation_model import LLMValidationModel
from adapters.validation_response_model import ValidationResponseModel
from configs.config import ApiKeyProvider, OllamaSettings, RoundRobinApiKeyProvider
from abc import ABC, abstractmethod
import io
from typing import TypeVar, Type
from pydantic import BaseModel
from PIL.Image import Image

import google.genai as genai
import httpx
import ollama
import truststore
import base64
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# TODO what about quality of images ?
# TODO what about thinking of model?
ResponseType = TypeVar("ResponseType", bound=BaseModel)

class LLMAdapter(ABC):
    @abstractmethod
    def generate_response(self, model: str, system_prompt: str, user_prompt: str, temperature: float = None, images: list[Image] = None, context_length: int = None, response_model: Type[ResponseType] = LLMValidationModel) -> ValidationResponseModel[ResponseType]:
        pass

class GeminiAdapter(LLMAdapter):
    def __init__(self, api_key_provider:ApiKeyProvider):
        self.api_key_provider = api_key_provider
        
    def generate_response(self, model: str, system_prompt: str, user_prompt: str, temperature: float = None, images: list[Image] = None, context_length: int = None, response_model: Type[ResponseType] = LLMValidationModel):
        validation_metadada = ValidationMetadataModel(
            validation_model=model,
            temperature=temperature,
            context_length=context_length,
            start_time=datetime.now(),
        )
        
        client = genai.Client(api_key=self.api_key_provider.get_api_key())
        
        config = {
                "system_instruction": system_prompt,
                "response_mime_type": "application/json",
                "response_schema": response_model,
                }
        # Only add temperature if it was explicitly provided
        if temperature is not None:
            config["temperature"] = temperature
        # Add context length limit if provided
        if context_length is not None:
            print("Context length is not supported in Gemini. There is only option to define max output length with max_output_tokens")

        contents = []
        contents.append(user_prompt)
        if images:
            contents.extend(images)
            
        response = client.models.generate_content(
            model=model,
            contents=contents,
            config=config
        )

        parsed_response = response.parsed

        validation_metadada.end_time = datetime.now()
        validation_metadada.duration = validation_metadada.end_time.timestamp() - validation_metadada.start_time.timestamp()

        validation_response = ValidationResponseModel(llm_validation_response=parsed_response, validation_metadata=validation_metadada)
        return validation_response


def _before_sleep_print(retry_state):
    print(
        f"Ollama request failed (attempt {retry_state.attempt_number}) due to: "
        f"{retry_state.outcome.exception()}. Retrying in {retry_state.upcoming_sleep:.1f}s..."
    )


class OllamaAdapter(LLMAdapter):
    def __init__(self, config: OllamaSettings):
        self.config = config
        # Windows-compatible SSL context
        ctx = truststore.SSLContext()
        
        # Basic auth only when credentials are configured (e.g. a shared server behind a proxy)
        auth = None
        if self.config.AUTH_USERNAME and self.config.AUTH_PASSWORD:
            auth = httpx.BasicAuth(self.config.AUTH_USERNAME, self.config.AUTH_PASSWORD)

        # set verify=ctx to use the Windows Certificate Store
        self.http_client = httpx.Client(
            verify=ctx,
            base_url=self.config.BASE_URL,
            auth=auth,
            timeout=100.0,
            follow_redirects=True
        )
        
    @retry(
        reraise=True,
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((
            httpx.HTTPError,
            ollama.RequestError,
            ollama.ResponseError
        )),
        before_sleep=_before_sleep_print
    )
    def generate_response(self, model: str, system_prompt: str, user_prompt: str, temperature: float = None, images: list[Image] = None, context_length: int = None, response_model: Type[ResponseType] = LLMValidationModel):
        validation_metadada = ValidationMetadataModel(
            validation_model=model,
            temperature=temperature,
            context_length=context_length,
            start_time=datetime.now(),
        )
        
        client = ollama.Client(host=self.config.BASE_URL)
        client._client = self.http_client
        
        ollama_images = None
        if images:
            ollama_images = []
            for img in images:
                buffered = io.BytesIO()
                img.save(buffered, format="JPEG")
                img_b64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
                ollama_images.append(img_b64)

        # Setup the options dictionary
        options = {}
        if temperature is not None:
            options["temperature"] = temperature
        if context_length is not None:
            options["num_ctx"] = context_length

        response = client.generate(
                    model=model,
                    system=system_prompt,
                    prompt=user_prompt,
                    images=ollama_images,
                    options=options, # If empty, ollama uses default
                    stream=False,
                    format=response_model.model_json_schema(),
                )
        # Extract both fields
        final_text = response.get('response', '')
        thinking_text = response.get('thinking', '')

        # If the final response is empty (common in Qwen 3.6), 
        # use the thinking field as the source of your JSON.
        if not final_text.strip() and thinking_text:
            parsed_response = response_model.model_validate_json(thinking_text)
        else:
            parsed_response = response_model.model_validate_json(final_text)
        validation_metadada.end_time = datetime.now()
        validation_metadada.duration = validation_metadada.end_time.timestamp() - validation_metadada.start_time.timestamp()
        validation_metadada.prompt_tokens = response.get('prompt_eval_count')
        validation_metadada.completion_tokens = response.get('eval_count')
        validation_metadada.total_duration = response.get('total_duration')

        validation_response = ValidationResponseModel(llm_validation_response=parsed_response, validation_metadata=validation_metadada)
        return validation_response

