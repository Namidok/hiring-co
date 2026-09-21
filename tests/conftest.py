import socket
import pytest

OLLAMA_HOST = "localhost"
OLLAMA_PORT = 11434


def _ollama_reachable() -> bool:
    try:
        with socket.create_connection((OLLAMA_HOST, OLLAMA_PORT), timeout=1):
            return True
    except OSError:
        return False


requires_ollama = pytest.mark.skipif(
    not _ollama_reachable(),
    reason="Ollama not reachable on localhost:11434 - these tests need a local "
           "LLM and don't run in CI (no Ollama runner available there).",
)