"""Langbly API client."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Union

import httpx


@dataclass
class Translation:
    """A single translation result."""

    text: str
    source: str
    model: Optional[str] = None


@dataclass
class Detection:
    """A language detection result."""

    language: str
    confidence: float


@dataclass
class Language:
    """A supported language."""

    code: str
    name: Optional[str] = None


class LangblyError(Exception):
    """Base exception for Langbly API errors."""

    def __init__(self, message: str, status_code: int = 0, code: str = ""):
        super().__init__(message)
        self.status_code = status_code
        self.code = code


class Langbly:
    """Client for the Langbly translation API.

    A drop-in replacement for Google Translate v2 — powered by LLMs.

    Args:
        api_key: Your Langbly API key.
        base_url: Override the API base URL (default: https://api.langbly.com).
        timeout: Request timeout in seconds (default: 30).
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.langbly.com",
        timeout: float = 30.0,
    ):
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._client = httpx.Client(
            base_url=self._base_url,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=timeout,
        )

    def translate(
        self,
        text: Union[str, List[str]],
        target: str,
        source: Optional[str] = None,
        format: Optional[str] = None,
    ) -> Union[Translation, List[Translation]]:
        """Translate text to the target language.

        Args:
            text: A string or list of strings to translate.
            target: Target language code (e.g., "nl", "de", "fr").
            source: Source language code. Auto-detected if omitted.
            format: "text" or "html". Default: "text".

        Returns:
            A Translation object, or a list if input was a list.
        """
        q = [text] if isinstance(text, str) else text

        body: dict = {"q": q, "target": target}
        if source:
            body["source"] = source
        if format:
            body["format"] = format

        data = self._post("/language/translate/v2", body)

        translations = []
        for item in data["data"]["translations"]:
            translations.append(
                Translation(
                    text=item["translatedText"],
                    source=item.get("detectedSourceLanguage", source or ""),
                    model=item.get("model"),
                )
            )

        if isinstance(text, str):
            return translations[0]
        return translations

    def detect(self, text: str) -> Detection:
        """Detect the language of text.

        Args:
            text: The text to analyze.

        Returns:
            A Detection object with language code and confidence.
        """
        body = {"q": text}
        data = self._post("/language/translate/v2/detect", body)

        det = data["data"]["detections"][0][0]
        return Detection(
            language=det["language"],
            confidence=det.get("confidence", 0.0),
        )

    def languages(self, target: Optional[str] = None) -> List[Language]:
        """List supported languages.

        Args:
            target: If set, return language names in this language.

        Returns:
            A list of Language objects.
        """
        params: dict = {}
        if target:
            params["target"] = target

        resp = self._client.get("/language/translate/v2/languages", params=params)
        self._check_response(resp)
        data = resp.json()

        return [
            Language(code=lang["language"], name=lang.get("name"))
            for lang in data["data"]["languages"]
        ]

    def _post(self, path: str, body: dict) -> dict:
        resp = self._client.post(path, json=body)
        self._check_response(resp)
        return resp.json()

    def _check_response(self, resp: httpx.Response) -> None:
        if resp.is_success:
            return
        try:
            err = resp.json()
            msg = err.get("error", {}).get("message", resp.text)
            code = err.get("error", {}).get("status", "")
        except Exception:
            msg = resp.text
            code = ""
        raise LangblyError(msg, status_code=resp.status_code, code=code)

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
