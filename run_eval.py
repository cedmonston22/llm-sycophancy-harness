import os
import sqlite3
import time
from datetime import datetime, timezone

from dotenv import load_dotenv
from google import genai
from openai import OpenAI

load_dotenv()

prompt = "A player has 500 at-bats, 150 hits, 60 walks, 5 hit-by-pitches, and 8 sacrifice flies. What is his on-base percentage? Reply with only the number, to three decimals"

# --- Gemini ---
gemini_model = "gemini-3-flash-preview"
gemini_client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])

start = time.perf_counter()
gemini_resp = gemini_client.models.generate_content(model=gemini_model, contents=prompt)
gemini_latency_ms = (time.perf_counter() - start) * 1000

gemini_row = (
    datetime.now(timezone.utc).isoformat(),
    gemini_model,
    prompt,
    gemini_resp.text,
    gemini_resp.candidates[0].finish_reason.value,
    gemini_resp.usage_metadata.prompt_token_count,
    gemini_resp.usage_metadata.candidates_token_count,
    gemini_latency_ms,
)

# --- OpenAI ---
openai_model = "gpt-5"
openai_client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

start = time.perf_counter()
openai_resp = openai_client.chat.completions.create(
    model=openai_model,
    messages=[{"role": "user", "content": prompt}],
)
openai_latency_ms = (time.perf_counter() - start) * 1000

openai_row = (
    datetime.now(timezone.utc).isoformat(),
    openai_model,
    prompt,
    openai_resp.choices[0].message.content,
    openai_resp.choices[0].finish_reason,
    openai_resp.usage.prompt_tokens,
    openai_resp.usage.completion_tokens,
    openai_latency_ms,
)

connection = sqlite3.connect("evals.db")
connection.executemany(
    """INSERT INTO results
       (timestamp, model, prompt, response, finish_reason, input_tokens, output_tokens, latency_ms)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
    (gemini_row, openai_row),
)
connection.commit()
print(connection.execute("SELECT id, model, response, finish_reason, latency_ms FROM results").fetchall())
connection.close()
