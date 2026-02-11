# langbly-python

[![PyPI](https://img.shields.io/pypi/v/langbly)](https://pypi.org/project/langbly/)
[![Python](https://img.shields.io/pypi/pyversions/langbly)](https://pypi.org/project/langbly/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Official Python SDK for the [Langbly](https://langbly.com) translation API — a drop-in replacement for Google Translate v2, powered by LLMs.

**5-10x cheaper than Google Translate** · **Better quality** · **Switch in one PR**

## Installation

```bash
pip install langbly
```

## Quick Start

```python
from langbly import Langbly

client = Langbly(api_key="your-api-key")

# Translate text
result = client.translate("Hello world", target="nl")
print(result.text)  # "Hallo wereld"

# Batch translate
results = client.translate(["Hello", "Goodbye"], target="nl")
for r in results:
    print(r.text)

# Detect language
detection = client.detect("Bonjour le monde")
print(detection.language)  # "fr"

# List supported languages
languages = client.languages(target="en")
```

## Migrate from Google Translate

Already using `google-cloud-translate`? Switching takes 2 minutes:

```python
# Before (Google Translate)
from google.cloud import translate_v2 as translate
client = translate.Client()
result = client.translate("Hello", target_language="nl")

# After (Langbly) — same concepts, better translations, 5x cheaper
from langbly import Langbly
client = Langbly(api_key="your-key")
result = client.translate("Hello", target="nl")
```

→ Full migration guide: [langbly.com/docs/migrate-google](https://langbly.com/docs/migrate-google)

## Features

- **Google Translate v2 API compatible** — same endpoint format
- **Auto-retry** — exponential backoff on 429/5xx with Retry-After support
- **Typed errors** — `RateLimitError`, `AuthenticationError`, `LangblyError`
- **Batch translation** — translate multiple texts in one request
- **Language detection** — automatic source language identification
- **HTML support** — translate HTML while preserving tags
- **Context manager** — use `with` for automatic cleanup

## Error Handling

```python
from langbly import Langbly, RateLimitError, AuthenticationError

client = Langbly(api_key="your-key")

try:
    result = client.translate("Hello", target="nl")
except AuthenticationError:
    print("Invalid API key")
except RateLimitError as e:
    print(f"Rate limited — retry after {e.retry_after}s")
```

## API Reference

### `Langbly(api_key, base_url=None, timeout=30.0, max_retries=2)`

Create a client instance.

- `api_key` (str): Your Langbly API key — [get one free](https://langbly.com/signup)
- `base_url` (str, optional): Override the API URL (default: `https://api.langbly.com`)
- `timeout` (float, optional): Request timeout in seconds (default: 30)
- `max_retries` (int, optional): Retries for transient errors (default: 2)

### `client.translate(text, target, source=None, format=None)`

- `text` (str | list[str]): Text(s) to translate
- `target` (str): Target language code (e.g., "nl", "de", "fr")
- `source` (str, optional): Source language code (auto-detected if omitted)
- `format` (str, optional): "text" or "html"

### `client.detect(text)`

- `text` (str): Text to analyze

### `client.languages(target=None)`

- `target` (str, optional): Language code to return names in

## Links

- [Website](https://langbly.com)
- [Documentation](https://langbly.com/docs)
- [Compare: Langbly vs Google vs DeepL](https://langbly.com/compare)
- [JavaScript/TypeScript SDK](https://github.com/Langbly/langbly-js)

## License

MIT
