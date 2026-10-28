
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

api_key = os.getenv("NVIDIA_API_KEY")
model = os.getenv("NVIDIA_MODEL")
base_url = os.getenv(
    "NVIDIA_BASE_URL",
    "https://integrate.api.nvidia.com/v1",
)

if not api_key or not model:
    raise SystemExit(
        "Missing NVIDIA_API_KEY or NVIDIA_MODEL in .env"
    )

client = OpenAI(
    api_key=api_key,
    base_url=base_url,
    timeout=60.0,
)

print(f"Testing model: {model}")

response = client.chat.completions.create(
    model=model,
    messages=[
        {
            "role": "user",
            "content": (
                "Reply with exactly: NVIDIA connection works"
            ),
        }
    ],
    max_tokens=40,
    temperature=0,
)

print("\nModel response:")
print(response.choices[0].message.content)
