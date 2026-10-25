# Local LMM Pipeline for Grading Handwritten Programming Exams

Source code, grading prompt, response schema and per-question scores accompanying the paper

> J. Paška, P. Zajac: *A Local Large Multimodal Model Pipeline for Grading Handwritten Programming Exams*. 2026 IEEE 18th International Scientific Conference on Informatics.

The pipeline grades scanned handwritten C programming exams with locally hosted, open-weight large multimodal models (Qwen3.6 and Gemma4 via [Ollama](https://ollama.com)) in a single, zero-shot call per submission. The model returns a transcription, a comment and a normalized score in [0, 1] for each of the eight exam questions.


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
| `script_example.py`, `examples/` | Example: one anonymized submission, its stored paper results, and a script to grade it |
| `script_example_name_matching.py`, `script_example_anonymization.py` | Examples of name matching and anonymization on one of your own (non-anonymized) submissions |
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

prints all grading-agreement statistics of the paper: the total-points agreement (Table III), the per-question correlations and mean differences (Table IV), standard deviations, ranges and bootstrap 95% confidence intervals of the differences, the paired comparison of Qwen3.6 and Gemma4, and the comparison of re-run submissions with the rest. Resampling uses a fixed seed, so the output is reproducible; no packages beyond the standard library are needed.

## Setup

Python 3.12+ and an Ollama server with the models used in the paper:

```
ollama pull qwen3.6
ollama pull gemma4:31b
pip install -r requirements.txt
cp .env.example .env   # server URL and optional credentials
```

The anonymization step also needs the [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) binary.

## Quick start: grade the example submission

`examples/000.pdf` is one anonymized submission (four scanned pages, eight questions), the one shown in Fig. 4 and Table I of the paper. To grade it with the configuration from the paper:

```
python script_example.py               # qwen3.6
python script_example.py gemma4:31b
```

The script prints, per question, the human score, the scores reported in the paper (`examples/expected/`) and the score of this run, and writes the JSON result and an HTML report to `examples/output/`. Small differences from the paper are expected: the example PDF is the anonymized (re-rendered) scan, not the original one, and model versions behind a tag can change.

In the HTML report, compare the transcription (*Extracted Text*) of question 1 with the scan: in the paper's run, Qwen3.6 added a line `buff[j] = '\0';` that the student did not write (see the Discussion section of the paper).

## Examples: name matching and anonymization

These need a submission with readable name fields and a class list, which are not part of the repository. Put them in git-ignored locations:

- `examples/private/<id>.pdf`: one submission, numbered by the student's index in the class list (e.g. `000.pdf` for the first student);
- `assignments/students.txt`: one name per line, in alphabetical order (see `examples/dummy_students.txt`).

**Run name matching with `--no-think`.** With the model's thinking mode enabled, current versions of the models can keep thinking on a single page until they hit the context limit or the HTTP timeout, without returning an answer.

```
python script_example_name_matching.py --no-think              # qwen3.6
python script_example_name_matching.py gemma4:31b --no-think
python script_example_anonymization.py
```

The name-matching script reports, for each page, the matched student, the confidence and whether the match is correct. The anonymization script writes `examples/private/output/<id>_anonymized.pdf`; check that the name is blacked out on every page.

## Running the pipeline

All scripts are run from the repository root. Data folders (git-ignored) are expected under `assignments/y2026/exam/`:

1. `raw_pdfs/`: scanned page collections, e.g. `b-k-1-2.pdf`. The page-to-student matching also needs `assignments/students.txt` (one name per line, see `examples/dummy_students.txt`):
   ```
   python -m assignments.y2026.exam.scripts.script_correlate_assignments
   ```
   The script runs with thinking disabled (`THINK = False`, see the previous section).
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
| Thinking mode | Ollama default (enabled); for name matching now disabled, see above |
| Context length | 32,768 tokens for grading, 8,192 for name matching |
| Temperature | 0; re-run of failed submissions at 0.05 (Qwen3.6: 5, Gemma4: 11 of 90) |
| Page images | rendered at ~288 DPI, grayscale, sent as JPEG |
| Hardware | 2× NVIDIA RTX PRO 6000 Blackwell (96 GB), 2× AMD EPYC 9135, 1 TB RAM |
