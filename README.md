# Local LMM Pipeline for Grading Handwritten Programming Exams

Source code, grading prompt, response schema and per-question scores accompanying the paper

> J. Paška, P. Zajac: *A Local Large Multimodal Model Pipeline for Grading Handwritten Programming Exams*. 2026 IEEE 18th International Scientific Conference on Informatics.

The pipeline grades scanned handwritten C programming exams with locally hosted, open-weight large multimodal models (Qwen3.6 and Gemma4 via [Ollama](https://ollama.com)) in a single, zero-shot call per submission. The model returns a transcription, a comment and a normalized score in [0, 1] for each of the eight exam questions.

The scanned exams are **not** included. They contain student handwriting and are released separately after anonymization.

## Contents

| Path | What it is |
|---|---|
| `assignments/y2026/exam/prompts/validation_prompt_2026_exam_v1.MD` | Grading prompt used in the paper (exam questions in Slovak) |
| `assignments/y2026/exam/prompts/Responses.py` | Response schema (`LLMValidationModel_exam2026_v1`) |
| `adapters/` | `LLMAdapter` interface with `OllamaAdapter` and `GeminiAdapter` |
| `agents/AssignmentValidatorAgent.py` | Grading agent (prompt + page images, one call per submission) |
| `script_basic.py` | Grading run: resumable batch over all submission PDFs |
| `script_generate_reports.py` | Per-submission HTML reports and CSV summary from stored JSON results |
| `agents/AssignmentOrganizer/`, `assignments/y2026/exam/scripts/script_correlate_assignments.py` | LMM-based matching of scanned pages to students (prompt, schema, script) |
| `assignments/y2026/exam/scripts/script_compare_csv.py` | Accuracy of the page-to-student matching against a manual assignment |
| `assignments/y2026/exam/scripts/generate_pdfs.py` | Assembles one PDF per student from the scanned collections |
| `helpers/anonymization.py` | OCR-based (Tesseract) redaction of the name field |
| `data/scores_per_question.csv` | Scores of the 90 evaluated submissions (see below) |
| `script_stats.py` | Recomputes the grading-agreement results of the paper from the CSV |

## Data: `data/scores_per_question.csv`

One row per evaluated submission (90 rows), identified only by an anonymous ID.

- `M1`–`M8`: human grader, `Q1`–`Q8`: Qwen3.6, `G1`–`G8`: Gemma4. Scores are normalized to [0, 1] per question (human points / 5), so a total score is at most 8.
- An empty cell means the model returned no valid entry for that question (one case: Gemma4, submission 034, question 3). It counts as 0 in the total and is left out of the correlations.
- `temperature_qwen`, `temperature_gemma`: sampling temperature of the call that produced the result. 0 in the first run; submissions that failed there were re-run at 0.05.

```
python script_stats.py
```

prints the total-points agreement (Table III of the paper) and the per-question Pearson correlations.

## Setup

Python 3.12+ and an Ollama server with the models used in the paper:

```
ollama pull qwen3.6
ollama pull gemma4:31b
pip install -r requirements.txt
cp .env.example .env   # server URL and optional credentials
```

The anonymization step also needs the [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) binary.

## Running the pipeline

All scripts are run from the repository root. Data folders (git-ignored) are expected under `assignments/y2026/exam/`:

1. `raw_pdfs/`: scanned page collections, e.g. `b-k-1-2.pdf`. The page-to-student matching also needs `assignments/students.txt` (one name per line, see `examples/dummy_students.txt`):
   ```
   python -m assignments.y2026.exam.scripts.script_correlate_assignments
   ```
2. `results-pairing/actual_assignments.csv`: the verified page-to-student assignment, from which
   ```
   python -m assignments.y2026.exam.scripts.generate_pdfs
   ```
   creates `generated_pdfs/` with one PDF per student.
3. Grading (set `USED_MODEL`, `TEMPERATURE` and `CURRENT_RUN` in the script):
   ```
   python script_basic.py
   python script_generate_reports.py
   ```
   Results are stored as one JSON file per submission in `results-validation/`. A run skips submissions that already have a result, so an interrupted or partly failed run can be repeated.

## Configuration used in the paper

| Setting | Value |
|---|---|
| Models (Ollama tags) | `qwen3.6` (36.0B MoE, Q4_K_M), `gemma4:31b` (31.3B, Q4_K_M) |
| Thinking mode | Ollama default (enabled) |
| Context length | 32,768 tokens |
| Temperature | 0; re-run of failed submissions at 0.05 (Qwen3.6: 5, Gemma4: 11 of 90) |
| Page images | rendered at ~288 DPI, grayscale, sent as JPEG |
| Hardware | 2× NVIDIA RTX PRO 6000 Blackwell (96 GB), 2× AMD EPYC 9135, 1 TB RAM |
