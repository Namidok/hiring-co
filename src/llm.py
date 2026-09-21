import json
import requests

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "qwen3:8b"


def ask_json(prompt: str, schema: dict) -> dict:
    """
    Send a prompt to the local Ollama model and get back JSON matching `schema`.
    Thinking mode disabled - we want the structured answer, not the reasoning trace.
    """
    body = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "format": schema,       # Ollama enforces this JSON schema on output
        "think": False,         # same thinking-mode issue as quant-bench
        "options": {"temperature": 0},
    }
    r = requests.post(OLLAMA_URL, json=body, timeout=120)
    r.raise_for_status()
    content = r.json()["message"]["content"]
    return json.loads(content)


if __name__ == "__main__":
    schema = {
        "type": "object",
        "properties": {"capital": {"type": "string"}},
        "required": ["capital"],
    }
    result = ask_json("What is the capital of Germany? Respond in the given JSON schema.", schema)
    print(result)