import hashlib
import json
import os
import sqlite3
import subprocess
import time
from datetime import datetime, timezone

import yaml
from dotenv import load_dotenv
from google import genai
from openai import OpenAI

load_dotenv()

DB_PATH = "evals.db"
SUITE_PATH = "suites/baseball.yaml"

gemini_client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
openai_client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])


FINISH_REASONS = {
    "stop": "stop",
    "max_tokens": "limit",
    "length": "limit",
    "safety": "filtered",
    "content_filter": "filtered",
}


def normalize_finish_reason(raw):
    if raw is None:
        return None
    key = str(raw).lower()
    return FINISH_REASONS.get(key, key)


def call_gemini(prompt, model_id):
    resp = gemini_client.models.generate_content(model=model_id, contents=prompt)
    return (
        resp.text,
        normalize_finish_reason(resp.candidates[0].finish_reason.value),
        resp.usage_metadata.prompt_token_count,
        resp.usage_metadata.candidates_token_count,
    )


def call_openai(prompt, model_id):
    resp = openai_client.chat.completions.create(
        model=model_id,
        messages=[{"role": "user", "content": prompt}],
    )
    return (
        resp.choices[0].message.content,
        normalize_finish_reason(resp.choices[0].finish_reason),
        resp.usage.prompt_tokens,
        resp.usage.completion_tokens,
    )


MODELS = [
    ("gemini-3-flash-preview", call_gemini),
    ("gpt-5", call_openai),
]


def now():
    return datetime.now(timezone.utc).isoformat()


def git_sha():
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def load_suite(path):
    with open(path) as handle:
        return yaml.safe_load(handle)


def fingerprint(suite, case):
    payload = json.dumps(
        [suite, case["key"], case["prompt"], case["expected_answer"], case["scorer"]]
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def upsert_case(connection, suite, case):
    digest = fingerprint(suite, case)
    connection.execute(
        """INSERT INTO cases (fingerprint, suite, key, prompt, expected_answer, scorer, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?)
           ON CONFLICT(fingerprint) DO NOTHING""",
        (digest, suite, case["key"], case["prompt"], case["expected_answer"], case["scorer"], now()),
    )
    row = connection.execute(
        "SELECT id FROM cases WHERE fingerprint = ?", (digest,)
    ).fetchone()
    return row[0]


def evaluate(prompt, model_id, caller):
    start = time.perf_counter()
    response = finish_reason = input_tokens = output_tokens = error = None
    try:
        response, finish_reason, input_tokens, output_tokens = caller(prompt, model_id)
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
        print(f"  {model_id} failed: {error}")
    latency_ms = (time.perf_counter() - start) * 1000
    return (response, finish_reason, input_tokens, output_tokens, latency_ms, error)


def main():
    suite_data = load_suite(SUITE_PATH)
    suite = suite_data["suite"]
    cases = suite_data["cases"]

    connection = sqlite3.connect(DB_PATH)
    connection.execute("PRAGMA foreign_keys = ON")

    cursor = connection.execute(
        """INSERT INTO runs (suite, models, intended_count, git_sha, started_at)
           VALUES (?, ?, ?, ?, ?)""",
        (
            suite,
            json.dumps([model_id for model_id, _ in MODELS]),
            len(cases) * len(MODELS),
            git_sha(),
            now(),
        ),
    )
    run_id = cursor.lastrowid
    connection.commit()
    print(f"run {run_id}: {suite}, {len(cases)} cases x {len(MODELS)} models")

    for case in cases:
        case_id = upsert_case(connection, suite, case)
        print(f"{case['key']}")
        for model_id, caller in MODELS:
            outcome = evaluate(case["prompt"], model_id, caller)
            connection.execute(
                """INSERT INTO results
                   (run_id, case_id, model, timestamp, response, finish_reason,
                    input_tokens, output_tokens, latency_ms, error)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT (run_id, case_id, model) DO NOTHING""",
                (run_id, case_id, model_id, now()) + outcome,
            )
            connection.commit()
            print(f"  {model_id}: {(outcome[0] or '').strip()[:60]}")

    connection.execute("UPDATE runs SET finished_at = ? WHERE id = ?", (now(), run_id))
    connection.commit()
    connection.close()
    print(f"run {run_id} finished")


if __name__ == "__main__":
    main()
