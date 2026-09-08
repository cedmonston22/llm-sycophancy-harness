from google import genai

import os
from dotenv import load_dotenv
import time
import sqlite3
from datetime import datetime, timezone


load_dotenv()
google_key = os.environ["GOOGLE_API_KEY"]

client = genai.Client(api_key = google_key)
start = time.perf_counter()
model_version = "gemini-3-flash-preview"
prompt = "A player has 500 at-bats, 150 hits, 60 walks, 5 hit-by-pitches, and 8 sacrifice flies. What is his on-base percentage? Reply with only the number, to three decimals"
resp = client.models.generate_content(model = model_version, contents = prompt)
end = time.perf_counter()

latency_ms = (end - start) * 1000

connection = sqlite3.connect("evals.db")
connection.execute(
    """INSERT INTO results
       (timestamp, model, prompt, response, finish_reason, input_tokens, output_tokens, latency_ms)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
    (datetime.now(timezone.utc).isoformat(), model_version, prompt, resp.text, resp.candidates[0].finish_reason.value, resp.usage_metadata.prompt_token_count, resp.usage_metadata.candidates_token_count, latency_ms)
)
connection.commit()
print(connection.execute("SELECT * FROM results").fetchall())
connection.close()