import os
from dotenv import load_dotenv

# load environment variables; groq api key, url of dummyjson
load_dotenv()

# Groq API key & URL
GROQ_API_KEY = os.getenv('GROQ_API_KEY', '')
GROQ_API_URL = os.getenv("GROQ_API_URL", "https://api.groq.com/v1")

# DummyJSON API base URL
DUMMYJSON_BASE_URL = os.getenv("DUMMYJSON_BASE_URL", "https://dummyjson.com")
