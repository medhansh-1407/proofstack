
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


def repair_code(source_code: str, task: str) -> str:
    """Ask NVIDIA Nemotron for a complete replacement Python file."""
    api_key = os.getenv("NVIDIA_API_KEY")
    model = os.getenv("NVIDIA_MODEL")
    base_url = os.getenv(
        "NVIDIA_BASE_URL",
        "https://integrate.api.nvidia.com/v1",
    )

    if not api_key or not model:
        raise RuntimeError(
            "Set NVIDIA_API_KEY and NVIDIA_MODEL in .env"
        )

    client = OpenAI(
        api_key=api_key,
        base_url=base_url,
        timeout=90.0,
    )

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a careful Python bug-fixing agent. "
                    "Return the complete corrected Python source file only. "
                    "Do not use Markdown fences or explanations. "
                    "Preserve unrelated behavior and make the smallest "
                    "reasonable fix."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Task: {task}\n\n"
                    f"Current Python source:\n{source_code}\n\n"
                    "Return the complete corrected source file."
                ),
            },
        ],
        temperature=0,
        max_tokens=1500,
    )

    content = response.choices[0].message.content
    if not content:
        raise RuntimeError("Nemotron returned an empty response")

    content = content.strip()

    # Remove a Markdown fence if the model adds one.
    if content.startswith("```"):
        lines = content.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        content = "\n".join(lines).strip()

    if not content:
        raise RuntimeError("Nemotron returned no usable Python source")

    return content
