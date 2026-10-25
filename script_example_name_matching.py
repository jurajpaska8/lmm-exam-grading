"""Matches each page of a non-anonymized submission to a student from the class list
with an LMM, as in step 4 of the paper (one call per page, temperature 0).

Needs real data that is NOT part of the repository (both paths are git-ignored):
    examples/private/<id>.pdf    one submission with readable name fields
    assignments/students.txt     class list, one name per line, alphabetical;
                                 line N (from 0) is the student with index N

Usage (from the repository root):
    python script_example_name_matching.py                 # qwen3.6, submission 000
    python script_example_name_matching.py gemma4:31b
    python script_example_name_matching.py qwen3.6 000
    python script_example_name_matching.py --no-think      # disable the model's thinking mode

With thinking enabled (the model default, as in the paper) a page can take minutes;
raise OLLAMA_TIMEOUT (seconds, default 100) in .env if calls time out.
"""
from agents.AssignmentOrganizer.AssignmentOrganizerResponse import AssignmentOrganizerResponseV1
from adapters.LLMAdapter import OllamaAdapter
from configs.config import OllamaSettings, LOCAL_MODEL_QWEN3
from agents.GenericAgent import GenericAgent
from helpers.pdf_processor import PDFProcessor
from helpers.prompt_builder import fill_prompt_template, load_prompt_template
from helpers.student_names_provider import StudentNamesProvider
import sys

NO_THINK = "--no-think" in sys.argv
args = [a for a in sys.argv[1:] if a != "--no-think"]
USED_MODEL = args[0] if len(args) > 0 else LOCAL_MODEL_QWEN3
SUBMISSION_ID = args[1] if len(args) > 1 else "000"
SUBMISSION_PDF = f"examples/private/{SUBMISSION_ID}.pdf"
STUDENTS_FILE = "assignments/students.txt"
PROMPT_PATH = "agents/AssignmentOrganizer/assignment_correlation_prompt_v1.MD"
TEMPERATURE : float = 0.0
# The paper used 8192 here; with thinking enabled, current model versions can use up the
# remaining context (a page image alone is ~2,400 tokens for Qwen3.6) before answering
CONTEXT_LENGTH : int = 8192 * 4
# As in the paper, the prompt lists only the half of the class (B-K or L-Z) the scan belongs to
FIRST_L_Z_INDEX = 63

# Submission files are numbered by the student's index in the class list
expected_idx = int(SUBMISSION_ID)
students = StudentNamesProvider(STUDENTS_FILE).get_students_as_list_ordered()
half = students[:FIRST_L_Z_INDEX] if expected_idx < FIRST_L_Z_INDEX else students[FIRST_L_Z_INDEX:]
prompt = fill_prompt_template(load_prompt_template(PROMPT_PATH), {
    "STUDENT_NAMES": [f"[{idx}: {name}]" for idx, name in half]
})

agent = GenericAgent(llm_adapter=OllamaAdapter(config=OllamaSettings(), think=False if NO_THINK else None))
pages = PDFProcessor._extract_page_images(SUBMISSION_PDF, first_page=1)
print(f"Matching {len(pages)} pages of {SUBMISSION_PDF} with {USED_MODEL} "
      f"(thinking {'off' if NO_THINK else 'model default'}, timeout {OllamaSettings.TIMEOUT:.0f} s) "
      f"against {len(half)} names; expected student index {expected_idx} ({students[expected_idx][1]})\n")

correct = 0
for page_number, page in enumerate(pages, start=1):
    response = agent.identify_student(
        scanned_image=page,
        user_prompt=prompt,
        temperature=TEMPERATURE,
        context_length=CONTEXT_LENGTH,
        llm_model=USED_MODEL,
        response_model=AssignmentOrganizerResponseV1
    )
    r = response.llm_validation_response
    ok = r.student_idx == expected_idx
    correct += ok
    flags = " blank" if r.is_blank_name else (" illegible" if r.is_illegible_name else "")
    print(f"Page {page_number}: {'OK   ' if ok else 'WRONG'} idx={r.student_idx:>3} name='{r.student_name}' "
          f"confidence={r.confidence_score:.2f}{flags} ({response.validation_metadata.duration:.1f} s)")

print(f"\n{correct}/{len(pages)} pages matched to the correct student")
