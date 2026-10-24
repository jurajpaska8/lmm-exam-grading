"""Grades the example submission examples/000.pdf and compares the result with
the human grader and with the results reported in the paper.

Usage (from the repository root):
    python script_example.py                # qwen3.6
    python script_example.py gemma4:31b

Submission 000 is the one shown in Fig. 4 and Table I of the paper. Output is
written to examples/output/ (JSON result and HTML report).
"""
from assignments.y2026.exam.prompts.Responses import LLMValidationModel_exam2026_v1
from adapters.LLMAdapter import OllamaAdapter
from configs.config import OllamaSettings, LOCAL_MODEL_QWEN3
from agents.AssignmentValidatorAgent import AssignmentValidatorAgent
from helpers.pdf_processor import PDFProcessor
from models.validation_summary import ValidationSummary
from visualizers.HtmlAssignmentVisualizer import HtmlAssignmentVisualizer
import csv
import json
import os
import sys

EXAMPLE_ID = "000"
EXAMPLE_PDF = f"examples/{EXAMPLE_ID}.pdf"
EXPECTED_FOLDER = "examples/expected"
OUTPUT_FOLDER = "examples/output"
SCORES_CSV = "data/scores_per_question.csv"
PROMPT_PATH = "assignments/y2026/exam/prompts/validation_prompt_2026_exam_v1.MD"
NUM_QUESTIONS = 8

# Same configuration as in the paper
USED_MODEL = sys.argv[1] if len(sys.argv) > 1 else LOCAL_MODEL_QWEN3
TEMPERATURE : float = 0.0
CONTEXT_LENGTH : int = 8192 * 4
SANITIZED_MODEL_NAME : str = USED_MODEL.replace(":", "-").replace("/", "-").replace("\\", "-")


def human_scores(example_id: str) -> list[float]:
    with open(SCORES_CSV, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            if row["id"] == example_id:
                return [float(row[f"M{i}"]) for i in range(1, NUM_QUESTIONS + 1)]
    raise ValueError(f"Submission {example_id} not found in {SCORES_CSV}")


def scores_by_question(response: LLMValidationModel_exam2026_v1) -> dict[str, float]:
    # Last entry per standard identifier wins, as in the paper
    return {v.subassignment_id: v.percentage for v in response.validations}


def expected_scores(model_name: str) -> dict[str, float] | None:
    path = os.path.join(EXPECTED_FOLDER, f"{EXAMPLE_ID}_{model_name}_validation.json")
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        summary = ValidationSummary[LLMValidationModel_exam2026_v1].model_validate(json.load(f))
    return scores_by_question(summary.llm_validation_response)


def fmt(value: float | None) -> str:
    return f"{value:.2f}" if value is not None else "-"


print(f"Grading {EXAMPLE_PDF} with {USED_MODEL} at {OllamaSettings.BASE_URL} ...")
validator = AssignmentValidatorAgent(llm_adapter=OllamaAdapter(config=OllamaSettings()), prompt_path=PROMPT_PATH)
images = PDFProcessor._extract_page_images(EXAMPLE_PDF, first_page=1)
response = validator.process(
    images=images,
    student_names="",  # the grading prompt does not use student names
    temperature=TEMPERATURE,
    context_length=CONTEXT_LENGTH,
    model=USED_MODEL,
    response_model=LLMValidationModel_exam2026_v1
)
summary = ValidationSummary[LLMValidationModel_exam2026_v1](
    validation_metadata=response.validation_metadata,
    llm_validation_response=response.llm_validation_response,
    filename=os.path.basename(EXAMPLE_PDF)
)

os.makedirs(OUTPUT_FOLDER, exist_ok=True)
json_path = os.path.join(OUTPUT_FOLDER, f"{EXAMPLE_ID}_{SANITIZED_MODEL_NAME}_validation.json")
with open(json_path, "w", encoding="utf-8") as f:
    f.write(summary.model_dump_json(indent=2))
html_path = os.path.join(OUTPUT_FOLDER, f"{EXAMPLE_ID}_{SANITIZED_MODEL_NAME}_result.html")
with open(html_path, "w", encoding="utf-8") as f:
    f.write(HtmlAssignmentVisualizer().visualize(images, EXAMPLE_PDF, summary))

human = human_scores(EXAMPLE_ID)
paper_qwen = expected_scores("qwen3.6")
paper_gemma = expected_scores("gemma4-31b")
this_run = scores_by_question(summary.llm_validation_response)

meta = summary.validation_metadata
print(f"\nDuration {meta.duration:.1f} s, prompt tokens {meta.prompt_tokens}, completion tokens {meta.completion_tokens}")
print(f"\n{'Question':<10}{'Human':>8}{'Paper Q':>9}{'Paper G':>9}{'This run':>10}")
for i in range(1, NUM_QUESTIONS + 1):
    rt = f"RT{i}"
    print(f"{rt:<10}{fmt(human[i - 1]):>8}{fmt(paper_qwen.get(rt)):>9}{fmt(paper_gemma.get(rt)):>9}{fmt(this_run.get(rt)):>10}")
totals = [sum(human), sum(paper_qwen.values()), sum(paper_gemma.values()), sum(this_run.get(f"RT{i}", 0.0) for i in range(1, NUM_QUESTIONS + 1))]
print(f"{'Total':<10}{totals[0]:>8.2f}{totals[1]:>9.2f}{totals[2]:>9.2f}{totals[3]:>10.2f}  (out of 8)")
print(f"\nStored: {json_path}\n        {html_path}")
