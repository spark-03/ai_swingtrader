import os
from openai import OpenAI
from dotenv import load_dotenv

# Load .env
load_dotenv()

# Read API key
api_key = os.getenv("OPENROUTER_API_KEY")

print("API KEY LOADED:", api_key[:10] if api_key else "NOT FOUND")

# Create client
client = OpenAI(
    api_key=api_key,
    base_url="https://openrouter.ai/api/v1"
)


def analyze_trade(stock_data):

    prompt = f"""
    Analyze this stock for intraday scalping.

    Stock Data:
    {stock_data}

    Return:
    1. Trade Direction
    2. Confidence
    3. Risk Level
    4. Short Reason

    Return JSON only.
    """

    try:

        response = client.chat.completions.create(
            model="qwen/qwen-2.5-7b-instruct",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        return response.choices[0].message.content

    except Exception as e:

        print("\nFULL ERROR:")
        print(e)

        return None