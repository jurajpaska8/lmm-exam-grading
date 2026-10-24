from agents.AssignmentOrganizer.AssignmentCollection import AssignmentCollection
from agents.AssignmentOrganizer.AssignmentOrganizerResponse import AssignmentOrganizerResponseV1
from configs.config import RoundRobinApiKeyProvider
from adapters.LLMAdapter import OllamaAdapter, GeminiAdapter
from configs.config import OllamaSettings, LOCAL_MODEL_QWEN3, LOCAL_MODEL_GEMMA4, GOOGLE_GEMINI_MODEL_FLASHLITE_2_5, GOOGLE_GEMINI_MODEL_FLASH_2_5
from agents.GenericAgent import GenericAgent
from helpers.pdf_processor import PDFProcessor
from helpers.prompt_builder import fill_prompt_template, load_prompt_template
from helpers.student_names_provider import StudentNamesProvider
import os
import datetime
import csv

# IoC and DI

USED_MODEL = LOCAL_MODEL_GEMMA4  # or LOCAL_MODEL_QWEN3, GOOGLE_GEMINI_MODEL_FLASH_2_5
if USED_MODEL.startswith("gemini"):
    llm_adapter = GeminiAdapter(api_key_provider=RoundRobinApiKeyProvider())
else:
    llm_adapter = OllamaAdapter(config=OllamaSettings())
ASSIGNMENT_FOLDER_ROOT = "assignments/y2026"
ASSIGNMENT_NAME = "exam"
PROMPT_VERSION = "v1"
TEMPERATURE : float = 0.0
CONTEXT_LENGTH : int = 8192  # Not supported in Gemini, only max_output_tokens which is not the same as context length, so we will not use it for now

# One student name per line, in alphabetical order (see examples/dummy_students.txt). Not part of the repository.
STUDENTS_FILE = "assignments/students.txt"
# The scans are split into two collections by surname (B-K and L-Z); index of the first L-Z student in STUDENTS_FILE
FIRST_L_Z_INDEX = 63

response_model = AssignmentOrganizerResponseV1
organizer_agent = GenericAgent(llm_adapter=llm_adapter)
student_names_provider = StudentNamesProvider(STUDENTS_FILE)
STUDENT_NAMES : list[tuple[int, str]] = student_names_provider.get_students_as_list_ordered()
STUDENT_NAMES_B_K : list[tuple[int, str]] = STUDENT_NAMES[:FIRST_L_Z_INDEX]
STUDENT_NAMES_L_Z : list[tuple[int, str]] = STUDENT_NAMES[FIRST_L_Z_INDEX:]

assignment_collection = [AssignmentCollection(student_name=name, student_idx=idx, files_pages=[]) for idx, name in STUDENT_NAMES]
blank_name_pages: list[tuple[str, int]] = []
illegible_name_pages: list[tuple[str, int]] = []
assignment_folder = os.path.join(ASSIGNMENT_FOLDER_ROOT, ASSIGNMENT_NAME, "raw_pdfs")  # scanned collections, e.g. b-k-1-2.pdf
results_folder = os.path.join(ASSIGNMENT_FOLDER_ROOT, ASSIGNMENT_NAME, "results-pairing")
os.makedirs(results_folder, exist_ok=True)
script_start_time : datetime = datetime.datetime.now()

pdf_files = [f for f in os.listdir(assignment_folder) if f.endswith(".pdf")]
print(f"Found {len(pdf_files)} PDF files in the assignment folder.")
pdf_files_paths = [os.path.join(assignment_folder, f) for f in pdf_files]

prompt_path = f"agents/AssignmentOrganizer/assignment_correlation_prompt_{PROMPT_VERSION}.MD"
prompt_template = load_prompt_template(prompt_path)
print(f"System prompt loaded.")

student_name_strings_b_k = [f"[{idx}: {name}]" for idx, name in STUDENT_NAMES_B_K]
prompt_b_k = fill_prompt_template(prompt_template, {
        "STUDENT_NAMES": student_name_strings_b_k
        })
print(f"System prompt created with student_names for B-K.")
student_name_strings_l_z = [f"[{idx}: {name}]" for idx, name in STUDENT_NAMES_L_Z]
prompt_l_z = fill_prompt_template(prompt_template, {
        "STUDENT_NAMES": student_name_strings_l_z
        })
print(f"System prompt created with student_names for L-Z.")



try:
    for current_pdf in pdf_files_paths:
        print(f"Processing file: {current_pdf}")
        if "b-k" in current_pdf:
            STUDENT_NAMES_TO_USE = STUDENT_NAMES_B_K
            prompt = prompt_b_k
        elif "l-z" in current_pdf:
            STUDENT_NAMES_TO_USE = STUDENT_NAMES_L_Z
            prompt = prompt_l_z
        else:
            raise ValueError(f"File name {current_pdf} does not contain valid student name range (b-k or l-z)")
        
        pdf_pages_as_images = PDFProcessor._extract_page_images(current_pdf, first_page=0, last_page=None)
        print(f"Extracted {len(pdf_pages_as_images)} images from assignment {current_pdf}.")
        for current_page, page_image in enumerate(pdf_pages_as_images):
            correlation_response = organizer_agent.identify_student(
                scanned_image=pdf_pages_as_images[current_page],
                user_prompt=prompt,
                temperature=TEMPERATURE,
                context_length=CONTEXT_LENGTH,
                llm_model=USED_MODEL,
                response_model=response_model
                )
            student_idx = correlation_response.llm_validation_response.student_idx
            is_blank_name = correlation_response.llm_validation_response.is_blank_name
            is_illegible_name = correlation_response.llm_validation_response.is_illegible_name
            if(student_idx != -1):
                assignment_collection[student_idx].files_pages.append((current_pdf, current_page))
            elif(is_blank_name):
                blank_name_pages.append((current_pdf, current_page))
            elif(is_illegible_name):
                illegible_name_pages.append((current_pdf, current_page))

            print(f"File {current_pdf} - Page {current_page}: Student: {correlation_response.llm_validation_response.student_name}, Student idx: {correlation_response.llm_validation_response.student_idx}, Confidence score: {correlation_response.llm_validation_response.confidence_score}")
        print(f"File {current_pdf} - finished processing all pages.")

except Exception as e:
    print(f"Error processing PDF files. Issue happened on File {current_pdf} and Page {current_page}: Exception: {e}")
finally:
    script_end_time : datetime = datetime.datetime.now()
    script_duration = script_end_time.timestamp() - script_start_time.timestamp()
    print(f"Script started at: {script_start_time}, ended at: {script_end_time}, duration: {script_duration} seconds")

# Generate CSV summary from `assignment_collection`
pdf_headers = [
    "b-k-1-2.pdf",
    "b-k-3-4.pdf",
    "b-k-5-6.pdf",
    "b-k-7-8.pdf",
    "l-z-1-2.pdf",
    "l-z-3-4.pdf",
    "l-z-5-6.pdf",
    "l-z-7-8.pdf",
]

SANITIZED_MODEL_NAME : str = USED_MODEL.replace(":", "-").replace("/", "-").replace("\\", "-")
csv_path = os.path.join(results_folder, f"paired_pages_to_students_{SANITIZED_MODEL_NAME}_{PROMPT_VERSION}_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.csv")
with open(csv_path, "w", newline="", encoding="utf-8") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["student_idx", "student_name"] + pdf_headers)

    def page_list_for_pdf(page_records):
        pages_by_pdf = []
        for header in pdf_headers:
            pages = [str(page) for (fp, page) in page_records if os.path.basename(fp).lower().endswith(header.lower()) or os.path.basename(fp).lower() == header.lower()]
            pages_by_pdf.append(";".join(pages) if pages else "-1")
        return pages_by_pdf

    for ac in assignment_collection:
        row = [ac.student_idx, ac.student_name] + page_list_for_pdf(ac.files_pages)
        writer.writerow(row)

    writer.writerow(["blank_name_pages", ""] + page_list_for_pdf(blank_name_pages))
    writer.writerow(["illegible_name_pages", ""] + page_list_for_pdf(illegible_name_pages))

print(f"Wrote assignment summary CSV to: {csv_path}")