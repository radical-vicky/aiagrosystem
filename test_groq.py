import os
from dotenv import load_dotenv
from groq import Groq

# Load environment variables
load_dotenv()

# Get API key
api_key = os.environ.get('GROQ_API_KEY')

print(f"API Key found: {'Yes' if api_key else 'No'}")

if api_key:
    try:
        client = Groq(api_key=api_key)
        
        response = client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=[
                {"role": "user", "content": "Say 'Groq API is working perfectly!'"}
            ],
            max_tokens=50
        )
        
        print("✅ SUCCESS:", response.choices[0].message.content)
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
else:
    print("❌ No API key found in .env file")