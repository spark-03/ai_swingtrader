from openai import OpenAI

client = OpenAI(
    api_key="k-5678ijklmnopabcd5678ijklmnopabcd5678ijkl"
)

response = client.chat.completions.create(
    model="gpt-5-codex",
    messages=[
        {
            "role": "user",
            "content": "Write a Python function to add two numbers"
        }
    ]
)

print(response.choices[0].message.content)