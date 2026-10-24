import os
from dotenv import load_dotenv
from itertools import cycle
from abc import ABC, abstractmethod


LOCAL_MODEL_QWEN3 = "qwen3.6" # OCR and Reasoning
LOCAL_MODEL_GEMMA4 = "gemma4:31b" # OCR and Reasoning
GOOGLE_GEMINI_MODEL_FLASHLITE_2_5 = "gemini-2.5-flash-lite" # OCR
GOOGLE_GEMINI_MODEL_FLASH_2_5 = "gemini-2.5-flash"

load_dotenv(dotenv_path=".env")

GEMINI_API_KEYS_STR = os.getenv("GEMINI_API_KEYS", "")


class ApiKeyProvider(ABC):
    @abstractmethod
    def get_api_key(self):
        pass

class RoundRobinApiKeyProvider(ApiKeyProvider):
    def __init__(self):
        # Parse the keys: format "key1:val1;key2:val2"
        key_pairs = [(pair.split(':')[0], pair.split(':')[1]) for pair in GEMINI_API_KEYS_STR.split(';') if pair.strip()]
        if not key_pairs:
            raise ValueError("No Gemini API keys configured. Set GEMINI_API_KEYS in .env (format name1:key1;name2:key2).")
        self.api_key_cycle = cycle(key_pairs)

    def get_api_key(self):
        api_key_pair = next(self.api_key_cycle)
        print(f"RoundRobinApiKeyProvider, Using API key: {api_key_pair[0]}")
        return api_key_pair[1]

class OllamaSettings:
    # Defaults to a local Ollama server without authentication; see .env.example
    BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    AUTH_USERNAME = os.getenv("OLLAMA_USERNAME")
    AUTH_PASSWORD = os.getenv("OLLAMA_PASSWORD")
