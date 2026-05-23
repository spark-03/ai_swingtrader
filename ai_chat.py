from openai import OpenAI

client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key="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"
)

completion = client.chat.completions.create(
    model="deepseek-ai/deepseek-v4-flash",
    messages=[
        {
            "role": "user",
            "content": "Create a Python RSI trading strategy"
        }
    ],
    temperature=1,
    top_p=0.95,
    max_tokens=2000,
    extra_body={
        "chat_template_kwargs": {
            "thinking": True,
            "reasoning_effort": "high"
        }
    },
    stream=True
)

for chunk in completion:
    delta = chunk.choices[0].delta.content

    if delta:
        print(delta, end="", flush=True)