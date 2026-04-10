"""
LLM abstraction — tries free/cheap providers first, falls back to Anthropic.

Priority order:
1. GEMINI_API_KEY  -> Google Gemini (free tier: ~1500 requests/day)
2. OLLAMA          -> Local Ollama if running (completely free)
3. ANTHROPIC_API_KEY -> Claude (paid)

Set GEMINI_API_KEY from https://aistudio.google.com/apikey (free, no card needed).
"""

import os
import requests

DEFAULT_MAX_TOKENS = 2000


def complete(prompt: str, max_tokens: int = DEFAULT_MAX_TOKENS) -> str:
    """Generate text using the best available provider."""
    if os.environ.get("GEMINI_API_KEY"):
        return _gemini(prompt, max_tokens)
    if _ollama_available():
        return _ollama(prompt, max_tokens)
    if os.environ.get("ANTHROPIC_API_KEY"):
        return _anthropic(prompt, max_tokens)
    raise RuntimeError(
        "No LLM provider available. Set one of:\n"
        "  export GEMINI_API_KEY=...  (free, from https://aistudio.google.com/apikey)\n"
        "  OR run Ollama locally (brew install ollama && ollama run llama3.1)\n"
        "  OR export ANTHROPIC_API_KEY=... (paid)"
    )


def provider_name() -> str:
    if os.environ.get("GEMINI_API_KEY"):
        return "Gemini (free tier)"
    if _ollama_available():
        return f"Ollama ({os.environ.get('OLLAMA_MODEL', 'llama3.1:8b')})"
    if os.environ.get("ANTHROPIC_API_KEY"):
        return "Anthropic Claude"
    return "none"


# ----- Gemini -----
def _gemini(prompt: str, max_tokens: int) -> str:
    from google import genai

    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    model = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config={"max_output_tokens": max_tokens, "temperature": 0.7},
    )
    return (response.text or "").strip()


# ----- Ollama -----
def _ollama_available() -> bool:
    try:
        r = requests.get("http://localhost:11434/api/tags", timeout=1)
        return r.status_code == 200
    except Exception:
        return False


def _ollama(prompt: str, max_tokens: int) -> str:
    model = os.environ.get("OLLAMA_MODEL", "llama3.1:8b")
    r = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {"num_predict": max_tokens, "temperature": 0.7},
        },
        timeout=300,
    )
    r.raise_for_status()
    return r.json().get("response", "").strip()


# ----- Anthropic -----
def _anthropic(prompt: str, max_tokens: int) -> str:
    import anthropic

    client = anthropic.Anthropic()
    response = client.messages.create(
        model=os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-20250514"),
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text.strip()


def extract_json(text: str) -> str:
    """Strip markdown code fences from a JSON response."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```", 2)[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()
    return text
