from google import genai

import os
from dotenv import load_dotenv
import time

load_dotenv()
google_key = os.environ["GOOGLE_API_KEY"]

print(len(google_key))