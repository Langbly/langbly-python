# langbly-python

Official Python SDK for the [Langbly](https://langbly.com) translation API — a drop-in replacement for Google Translate v2.

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
```

## Google Translate Migration

If you're using `google-cloud-translate`, switching is simple:

```python
# Before (Google)
from google.cloud import translate_v2 as translate
client = translate.Client()
result = client.translate("Hello", target_language="nl")

# After (Langbly)
from langbly import Langbly
client = Langbly(api_key="your-key")
result = client.translate("Hello", target="nl")
```

## API Reference

### `Langbly(api_key, base_url=None)`

Create a client instance.

- `api_key` (str): Your Langbly API key
- `base_url` (str, optional): Override the API URL (default: `https://api.langbly.com`)

### `client.translate(text, target, source=None, format=None)`

Translate text.

- `text` (str | list[str]): Text(s) to translate
- `target` (str): Target language code (e.g., "nl", "de", "fr")
- `source` (str, optional): Source language code (auto-detected if omitted)
- `format` (str, optional): "text" or "html"

### `client.detect(text)`

Detect the language of text.

- `text` (str): Text to analyze

### `client.languages(target=None)`

List supported languages.

- `target` (str, optional): Language code to return names in

## License

MIT
