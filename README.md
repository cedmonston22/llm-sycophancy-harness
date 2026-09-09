# LLM Eval Harness

An evaluation harness that runs a suite of prompts across multiple LLMs and
records what each one returned, along with token usage and latency.

## Setup

```bash
py -m venv .venv
```

```bash
.venv\Scripts\python.exe -m pip install google-genai openai python-dotenv pyyaml
```

Create a `.env` in the project root:

```
GOOGLE_API_KEY=your-key-here
OPENAI_API_KEY=your-key-here
```

## Usage

Create the database and its tables. Run once.

```bash
.venv\Scripts\python.exe init_db.py
```

Run the suite in `suites/baseball.yaml` against every configured model.

```bash
.venv\Scripts\python.exe run_eval.py
```

## Suites

A suite is a YAML file of cases. A case is a prompt, the correct answer, and
how that answer should be checked.

```yaml
suite: baseball

cases:
  - key: obp-basic
    scorer: numeric
    expected_answer: "0.375"
    prompt: |
      A player has 500 at-bats, 150 hits, 60 walks, 5 hit-by-pitches,
      and 8 sacrifice flies. What is his on-base percentage?
      Reply with only the number, to three decimals.
```

## Schema

Three tables. A run is one invocation of the harness, a case is one prompt, and
a result is one model's answer to one case in one run.

### `runs`

| Column | Type | Nullable |
|---|---|---|
| `id` | INTEGER PRIMARY KEY | no |
| `suite` | TEXT | no |
| `models` | TEXT (JSON array) | no |
| `intended_count` | INTEGER | no |
| `git_sha` | TEXT | yes |
| `started_at` | TEXT (ISO-8601, UTC) | no |
| `finished_at` | TEXT (ISO-8601, UTC) | yes |

`finished_at` is written only when a run completes, so a run that crashed is
identifiable by a null `finished_at` with a stale `started_at`. A dying process
cannot record that it died, so completion is tracked by absence rather than by a
flag. `intended_count` and `models` record what the run was *supposed* to do,
which is what makes missing work detectable — results that were never produced
leave no rows to inspect.

### `cases`

| Column | Type | Nullable |
|---|---|---|
| `id` | INTEGER PRIMARY KEY | no |
| `fingerprint` | TEXT UNIQUE | no |
| `suite` | TEXT | no |
| `key` | TEXT | no |
| `prompt` | TEXT | no |
| `expected_answer` | TEXT | no |
| `scorer` | TEXT | no |
| `created_at` | TEXT (ISO-8601, UTC) | no |

Cases are immutable and content-addressed. `fingerprint` is a SHA-256 over the
suite, key, prompt, expected answer, and scorer — everything that determines a
result except the model. Editing any of those inserts a new row rather than
updating the old one, so historical results always point at the exact text that
produced them. `key` stays stable across edits, so a case can still be tracked
over time even as its wording changes.

### `results`

| Column | Type | Nullable |
|---|---|---|
| `id` | INTEGER PRIMARY KEY | no |
| `run_id` | INTEGER → `runs.id` | no |
| `case_id` | INTEGER → `cases.id` | no |
| `model` | TEXT | no |
| `timestamp` | TEXT (ISO-8601, UTC) | no |
| `response` | TEXT | yes |
| `finish_reason` | TEXT | yes |
| `input_tokens` | INTEGER | yes |
| `output_tokens` | INTEGER | yes |
| `latency_ms` | REAL | no |
| `error` | TEXT | yes |

`UNIQUE (run_id, case_id, model)` is the natural key: one model, one case, one
run, exactly one row. Re-running cannot duplicate.

Everything the API returns is nullable, because a failed call produces none of
it — the table has to be able to hold a failure. `latency_ms` is not nullable,
because a call that fails is still timed, and how long a failure took is useful.
`error` holds the exception type and message when a call fails; a failed eval is
data, not an outage.

`finish_reason` is normalized across providers to `stop`, `limit`, or
`filtered`. Gemini reports `MAX_TOKENS` and OpenAI reports `length` for the same
condition, so querying for truncated responses would otherwise miss one provider
entirely. Unrecognized values pass through lowercased rather than being dropped.
