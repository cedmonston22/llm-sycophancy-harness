from google import genai

import os
from dotenv import load_dotenv
import time

load_dotenv()
google_key = os.environ["GOOGLE_API_KEY"]

client = genai.Client(api_key = google_key)
start = time.perf_counter()
response = client.models.generate_content(model = "gemini-3-flash-preview", contents = "A player has 500 at-bats, 150 hits, 60 walks, 5 hit-by-pitches, and 8 sacrifice flies. What is his on-base percentage? Reply with only the number, to three decimals")
end = time.perf_counter()

latency_ms = (end - start) * 1000
print(response)
print(f"Total milliseconds: {latency_ms}")
