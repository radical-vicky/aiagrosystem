import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

api_key = os.environ.get('OPENAI_API_KEY')
print(f"API Key found: {'Yes' if api_key else 'No'}")

if api_key:
    client = OpenAI(api_key=api_key)
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": "Say 'OpenAI API is working correctly!'"}
        ],
        max_tokens=50
    )
    
    print("Response:", response.choices[0].message.content)
else:
    print("Please add OPENAI_API_KEY to your .env file")