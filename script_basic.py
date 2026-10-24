from assignments.y2026.exam.prompts.Responses import LLMValidationModel_exam2026_v1
from adapters.LLMAdapter import OllamaAdapter
from configs.config import OllamaSettings, LOCAL_MODEL_QWEN3, LOCAL_MODEL_GEMMA4
from agents.AssignmentValidatorAgent import AssignmentValidatorAgent
from helpers.pdf_processor import PDFProcessor
from models.validation_summary import ValidationSummary
import os
import datetime
import json


# Custom JSON encoder to handle datetime objects
class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        return super().default(obj)

print("Starting the grading app...")

# IoC and DI
# For the Gemini API use instead:
# from adapters.LLMAdapter import GeminiAdapter
# from configs.config import RoundRobinApiKeyProvider, GOOGLE_GEMINI_MODEL_FLASH_2_5
# USED_MODEL = GOOGLE_GEMINI_MODEL_FLASH_2_5
# llm_client = GeminiAdapter(api_key_provider=RoundRobinApiKeyProvider())

USED_MODEL = LOCAL_MODEL_QWEN3  # or LOCAL_MODEL_GEMMA4
ASSIGNMENT_FOLDER_ROOT = "assignments/y2026/exam"
ASSIGNMENT_NAME = "generated_pdfs"  # one PDF per submission (4 scanned pages)
PROMPT_VERSION = "validation_prompt_2026_exam_v1.MD"
VALIDATION_PROMPT_PATH = f"{ASSIGNMENT_FOLDER_ROOT}/prompts/{PROMPT_VERSION}"

llm_client = OllamaAdapter(config=OllamaSettings())
validator = AssignmentValidatorAgent(llm_adapter=llm_client, prompt_path=f"{VALIDATION_PROMPT_PATH}")

# Temperature 0 in the first run of a batch. Submissions that failed are re-run
# (same CURRENT_RUN, so finished results are kept) with a slightly higher temperature, e.g. 0.05.
TEMPERATURE : float = 0.00
CONTEXT_LENGTH : int = 8192 * 4 # Not supported in Gemini, only max_output_tokens which is not the same as context length
CURRENT_RUN : int = 1
# Sanitize model name to remove invalid Windows filename characters
SANITIZED_MODEL_NAME : str = USED_MODEL.replace(":", "-").replace("/", "-").replace("\\", "-")
RESULTS_FOLDER_NAME : str = f"reviewer-results-{SANITIZED_MODEL_NAME}-run-{CURRENT_RUN}"
RESULTS_FOLDER_PATH : str = f"{ASSIGNMENT_FOLDER_ROOT}/results-validation/{RESULTS_FOLDER_NAME}"

if not os.path.exists(RESULTS_FOLDER_PATH):
    os.makedirs(RESULTS_FOLDER_PATH)

assignment_folder = os.path.join(ASSIGNMENT_FOLDER_ROOT, ASSIGNMENT_NAME)
validation_summaries : list[ValidationSummary[LLMValidationModel_exam2026_v1]] = []

# Resumable runs: only submissions without a stored result are processed
pdf_files = [f for f in sorted(os.listdir(assignment_folder)) if f.endswith(".pdf")]
unprocessed_files = []
for f in pdf_files:
    base_name = os.path.splitext(f)[0]
    llm_json_path = os.path.join(RESULTS_FOLDER_PATH, f"{base_name}_validation.json")
    if not os.path.exists(llm_json_path):
        print(f"Adding file to processing {f}")
        unprocessed_files.append(f)

for filename in unprocessed_files:
    try:
        pdf_path = os.path.join(assignment_folder, filename)
        print(f"Extracting images from assignment {pdf_path}...")
        START_PAGE = 1

        pdf_pages_as_images = PDFProcessor._extract_page_images(pdf_path, first_page=START_PAGE)
        print(f"Extracted {len(pdf_pages_as_images)} images from assignment {pdf_path}.")
        print(f"Starting assignment validation pdf pages {pdf_path}...")
        validator_response = validator.process(
            images=pdf_pages_as_images,
            student_names="",  # the grading prompt does not use student names
            temperature=TEMPERATURE,
            context_length=CONTEXT_LENGTH,
            model=USED_MODEL,
            response_model=LLMValidationModel_exam2026_v1
        )
        print(f"Validator Response for {pdf_path} generated")

        validation_summary: ValidationSummary[LLMValidationModel_exam2026_v1] = ValidationSummary[LLMValidationModel_exam2026_v1](
            validation_metadata=validator_response.validation_metadata,
            llm_validation_response=validator_response.llm_validation_response,
            filename=filename
        )
        validation_summaries.append(validation_summary)

        # Store JSON response and metadata for later analysis
        llm_data = validation_summary.model_dump()
        base_name = os.path.splitext(filename)[0]
        llm_json_path = os.path.join(RESULTS_FOLDER_PATH, f"{base_name}_validation.json")
        with open(llm_json_path, "w", encoding="utf-8") as f:
            json.dump(llm_data, f, indent=2, ensure_ascii=False, cls=DateTimeEncoder)
        print(f"Stored LLM validation JSON: {llm_json_path}")

    except Exception as e:
        print(f"An error occurred during processing. Processed assignment: {filename}. Exception: {e}")

    finally:
        print(f"Assignment validation process completed. Processed assignment: {filename}.")
