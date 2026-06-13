from dotenv import load_dotenv
import anthropic

load_dotenv()

try:
    client = anthropic.Anthropic()
    print("Testing available models...")
    
    # Try to call messages with a simple test
    message = client.messages.create(
        model="claude-3-haiku-20240307",  # Try oldest Haiku
        max_tokens=100,
        messages=[{"role": "user", "content": "test"}],
    )
    print("✅ API call succeeded!")
    print(f"Response: {message.content[0].text[:50]}...")
except Exception as e:
    print(f"❌ Error: {e}")
