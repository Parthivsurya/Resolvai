"""Thin client around the local Ollama server.

All generation (answers + query rewriting) goes through :func:`generate`. deepseek-style
``<think>...</think>`` traces are stripped so downstream text stays clean regardless of the
model configured.
"""
from __future__ import annotations

import re

from .. import config

_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL)


def generate(prompt: str, system: str | None = None, temperature: float = 0.2) -> str:
    """Send a single-turn prompt to Ollama and return the model's text."""
    import ollama

    client = ollama.Client(host=config.OLLAMA_HOST)
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    resp = client.chat(
        model=config.OLLAMA_MODEL,
        messages=messages,
        options={"temperature": temperature},
    )
    text = resp["message"]["content"]
    return _THINK_RE.sub("", text).strip()
