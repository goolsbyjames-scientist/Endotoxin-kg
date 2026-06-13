from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv("ANTHROPIC_API_KEY")
print(f"API Key loaded: {bool(api_key)}")
if api_key:
    print(f"Key preview: {api_key[:20]}...")
    print(f"Key length: {len(api_key)}")
