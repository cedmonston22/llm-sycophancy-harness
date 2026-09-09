# LLM Eval Harness

An evaluation harness that runs a fixed set of prompts across multiple LLMs, records what each one returned, and allows you to compare outputs.

## Setup

```bash
py -m venv .venv
```

```bash
.venv\Scripts\python.exe -m pip install google-genai python-dotenv
```

```
GOOGLE_API_KEY = your-key-here
```

## Usage

Create the database and `results` table. Run once.

```bash
.venv\Scripts\python.exe init_db.py
```

Send the prompt to Gemini and record the result.

```bash
.venv\Scripts\python.exe gemini_call.py
```

## Schema

`results` — one row per model response.

| Column | Type | Nullable |
|---|---|---|---|
| `id` | INTEGER PRIMARY KEY| no |
| `timestamp` | TEXT (ISO-8601, UTC )| no | 
| `model` | TEXT | no | 
| `prompt` | TEXT | no | 
| `response` | TEXT | yes |
| `finish_reason` | TEXT | yes |
| `input_tokens` | INTEGER | yes |
| `output_tokens` | INTEGER | yes |
| `latency_ms` | REAL | no |

