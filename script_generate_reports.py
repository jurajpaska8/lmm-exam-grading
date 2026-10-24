from assignments.y2026.exam.prompts.Responses import LLMValidationModel_exam2026_v1
from helpers.prompt_builder import load_prompt_template
from configs.config import LOCAL_MODEL_QWEN3, LOCAL_MODEL_GEMMA4
from helpers.pdf_processor import PDFProcessor
from visualizers.HtmlAssignmentVisualizer import HtmlAssignmentVisualizer
from visualizers.CsvSummaryGenerator import CsvSummaryGenerator
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

CONTEXT_LENGTH : int = 8192 * 4
ASSIGNMENT_FOLDER_ROOT = "assignments/y2026/exam"
USED_MODEL = LOCAL_MODEL_QWEN3
VALIDATION_PROMPT_PATH = f"{ASSIGNMENT_FOLDER_ROOT}/prompts/validation_prompt_2026_exam_v1.MD"
CURRENT_RUN : int = 1
# Sanitize model name to remove invalid Windows filename characters
SANITIZED_MODEL_NAME : str = USED_MODEL.replace(":", "-").replace("/", "-").replace("\\", "-")
RESULTS_FOLDER_NAME : str = f"reviewer-results-{SANITIZED_MODEL_NAME}-run-{CURRENT_RUN}"
RESULTS_FOLDER_PATH : str = f"{ASSIGNMENT_FOLDER_ROOT}/results-validation/{RESULTS_FOLDER_NAME}"
PDFS_FOLDER : str = f"{ASSIGNMENT_FOLDER_ROOT}/generated_pdfs"

html_visualizer = HtmlAssignmentVisualizer()
csv_generator = CsvSummaryGenerator()

prompt_template = load_prompt_template(VALIDATION_PROMPT_PATH)

html_files : list[str] = []
validation_summaries : list[ValidationSummary[LLMValidationModel_exam2026_v1]] = []

for filename in sorted(os.listdir(RESULTS_FOLDER_PATH)):
    if filename.endswith("_validation.json"):
        file_path = os.path.join(RESULTS_FOLDER_PATH, filename)
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            validation_summaries.append(ValidationSummary[LLMValidationModel_exam2026_v1].model_validate(data))
start_time_of_first_file = validation_summaries[0].validation_metadata.start_time
end_time_of_last_file = validation_summaries[-1].validation_metadata.end_time

print("Generating CSV summary...")
csv_content = csv_generator.generate_csv(validation_summaries)
if csv_content:
    csv_path = os.path.join(RESULTS_FOLDER_PATH, "report.csv")
    with open(csv_path, "w", encoding="utf-8") as f:
        f.write(csv_content)
    print(f"Generated CSV summary: {csv_path}")
print("Generating CSV summary ended.")


print("Generating all pdfs")
for summary in validation_summaries:
    images = PDFProcessor._extract_page_images(os.path.join(PDFS_FOLDER, summary.filename), first_page=1)
    html_content = html_visualizer.visualize(images, summary.filename, summary)
    html_path = os.path.join(RESULTS_FOLDER_PATH, f"{summary.filename}_result.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    html_files.append(f"{summary.filename}_result.html")
    print(f"Generated HTML: {html_path}")

print("Generating front page summary...")
front_page_html = html_visualizer.generate_front_page(
    model=USED_MODEL,
    folder=PDFS_FOLDER,
    start_time=start_time_of_first_file.strftime('%Y-%m-%d %H:%M:%S'),
    end_time=end_time_of_last_file.strftime('%Y-%m-%d %H:%M:%S'),
    successful_count=len(html_files),
    prompt_text=prompt_template,
    parsed_files=html_files
)
front_page_path = os.path.join(RESULTS_FOLDER_PATH, "index.html")        
with open(front_page_path, "w", encoding="utf-8") as f:
    f.write(front_page_html)
    
print(f"Generated front page: {front_page_path}")


