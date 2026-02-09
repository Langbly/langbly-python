"""Langbly API client."""

from __future__ import annotations

import time
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


class RateLimitError(LangblyError):
    """Raised when the API returns 429 Too Many Requests."""

    def __init__(self, message: str, retry_after: Optional[float] = None):
        super().__init__(message, status_code=429, code="RATE_LIMITED")
        self.retry_after = retry_after


class AuthenticationError(LangblyError):
    """Raised when the API key is invalid or missing."""

    def __init__(self, message: str):
        super().__init__(message, status_code=401, code="UNAUTHENTICATED")


_RETRIABLE_STATUS_CODES = frozenset({429, 500, 502, 503, 504})


class Langbly:
    """Client for the Langbly translation API.

    A drop-in replacement for Google Translate v2 — powered by LLMs.

    Args:
        api_key: Your Langbly API key.
        base_url: Override the API base URL (default: https://api.langbly.com).
        timeout: Request timeout in seconds (default: 30).
        max_retries: Number of retries for transient errors (default: 2).
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.langbly.com",
        timeout: float = 30.0,
        max_retries: int = 2,
    ):
        if not api_key:
            raise ValueError("api_key is required")

        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._max_retries = max_retries
        self._client = httpx.Client(
            base_url=self._base_url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "User-Agent": "langbly-python/0.1.0",
            },
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

        Raises:
            LangblyError: On API error.
            RateLimitError: When rate limited (429).
            AuthenticationError: When API key is invalid (401).
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

        Raises:
            LangblyError: On API error.
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

        Raises:
            LangblyError: On API error.
        """
        params: dict = {}
        if target:
            params["target"] = target

        resp = self._request("GET", "/language/translate/v2/languages", params=params)
        data = resp.json()

        return [
            Language(code=lang["language"], name=lang.get("name"))
            for lang in data["data"]["languages"]
        ]

    def _post(self, path: str, body: dict) -> dict:
        resp = self._request("POST", path, json=body)
        return resp.json()

    def _request(
        self,
        method: str,
        path: str,
        **kwargs,
    ) -> httpx.Response:
        """Make an HTTP request with automatic retries for transient errors."""
        last_exc: Optional[Exception] = None

        for attempt in range(self._max_retries + 1):
            try:
                resp = self._client.request(method, path, **kwargs)
            except httpx.TimeoutException as exc:
                last_exc = exc
                if attempt < self._max_retries:
                    time.sleep(self._backoff_delay(attempt))
                    continue
                raise LangblyError(
                    f"Request timed out after {self._max_retries + 1} attempts",
                    status_code=0,
                    code="TIMEOUT",
                ) from exc
            except httpx.ConnectError as exc:
                last_exc = exc
                if attempt < self._max_retries:
                    time.sleep(self._backoff_delay(attempt))
                    continue
                raise LangblyError(
                    f"Connection failed after {self._max_retries + 1} attempts",
                    status_code=0,
                    code="CONNECTION_ERROR",
                ) from exc

            if resp.is_success:
                return resp

            # Don't retry client errors (except 429)
            if resp.status_code not in _RETRIABLE_STATUS_CODES:
                self._raise_for_status(resp)

            # Retriable error
            if attempt < self._max_retries:
                delay = self._get_retry_delay(resp, attempt)
                time.sleep(delay)
                continue

            # Final attempt failed
            self._raise_for_status(resp)

        # Should not reach here, but just in case
        if last_exc:
            raise last_exc
        raise LangblyError("Request failed")

    def _raise_for_status(self, resp: httpx.Response) -> None:
        """Parse error response and raise appropriate exception."""
        try:
            err = resp.json()
            msg = err.get("error", {}).get("message", resp.text)
            code = err.get("error", {}).get("status", "")
        except Exception:
            msg = resp.text or resp.reason_phrase
            code = ""

        if resp.status_code == 401:
            raise AuthenticationError(msg)
        if resp.status_code == 429:
            retry_after = self._parse_retry_after(resp)
            raise RateLimitError(msg, retry_after=retry_after)

        raise LangblyError(msg, status_code=resp.status_code, code=code)

    @staticmethod
    def _parse_retry_after(resp: httpx.Response) -> Optional[float]:
        """Parse Retry-After header if present."""
        header = resp.headers.get("retry-after")
        if header is None:
            return None
        try:
            return float(header)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _get_retry_delay(resp: httpx.Response, attempt: int) -> float:
        """Calculate retry delay, respecting Retry-After header."""
        retry_after = resp.headers.get("retry-after")
        if retry_after:
            try:
                return min(float(retry_after), 30.0)
            except (ValueError, TypeError):
                pass
        return min(0.5 * (2**attempt), 10.0)

    @staticmethod
    def _backoff_delay(attempt: int) -> float:
        """Exponential backoff delay for connection/timeout errors."""
        return min(0.5 * (2**attempt), 10.0)

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def __repr__(self) -> str:
        return f"Langbly(base_url={self._base_url!r})"
