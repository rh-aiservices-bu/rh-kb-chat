"""LangChain embeddings client for an OpenAI-compatible LiteLLM endpoint."""

from numbers import Real

import requests
from langchain_core.embeddings import Embeddings


class LiteLLMEmbeddings(Embeddings):
    """Generate embeddings through LiteLLM's OpenAI-compatible API."""

    def __init__(self, api_url: str, api_key: str, model_name: str):
        self.api_url = api_url
        self.api_key = api_key
        self.model_name = model_name

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        response = requests.post(
            self.api_url,
            headers={
                "accept": "application/json",
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            json={
                "encoding_format": "float",
                "input": texts,
                "model": self.model_name,
            },
            timeout=120,
        )

        if not response.ok:
            raise RuntimeError(
                f"Embedding endpoint returned HTTP {response.status_code}: "
                f"{response.text[:500]}"
            )

        payload = response.json()
        if isinstance(payload, dict) and isinstance(payload.get("data"), list):
            data = sorted(payload["data"], key=lambda item: item.get("index", 0))
            payload = [item.get("embedding") for item in data]

        valid = (
            isinstance(payload, list)
            and len(payload) == len(texts)
            and all(
                isinstance(vector, list)
                and vector
                and all(isinstance(value, Real) for value in vector)
                for vector in payload
            )
        )
        if not valid:
            raise RuntimeError(
                "Embedding endpoint returned an invalid response; expected "
                f"{len(texts)} numeric vector(s), received: {repr(payload)[:500]}"
            )

        return payload

    def embed_query(self, text: str) -> list[float]:
        return self.embed_documents([text])[0]
