"""
Test script to verify OpenAI API connection
"""
import os
from dotenv import load_dotenv
import openai

# Load environment variables
load_dotenv()

# Get API key from environment
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    print("❌ ERROR: OPENAI_API_KEY not found in environment variables")
    exit(1)

print(f"✅ OpenAI API Key found: {api_key[:20]}...")

# Initialize OpenAI client
try:
    client = openai.OpenAI(api_key=api_key)
    
    # Test connection with a simple request
    print("🔄 Testing OpenAI API connection...")
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": "Say 'Connection successful' if you can read this."}
        ],
        max_tokens=10
    )
    
    result = response.choices[0].message.content
    print(f"✅ Connection successful! Response: {result}")
    print("✅ OpenAI API connection established and working!")
    
except openai.AuthenticationError:
    print("❌ ERROR: Authentication failed. Please check your API key.")
    exit(1)
except openai.APIError as e:
    print(f"❌ ERROR: API error occurred: {e}")
    exit(1)
except Exception as e:
    print(f"❌ ERROR: Unexpected error: {e}")
    exit(1)

