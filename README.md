# Stremio Addon Framework [![Version](https://img.shields.io/pypi/v/Stremio?style=flat&logo=pypi)](https://pypi.org/project/Stremio) ![Python Version](https://img.shields.io/badge/Python-3.9%2B-blue.svg) [![Downloads](https://static.pepy.tech/personalized-badge/stremio?period=month&units=none&left_color=grey&right_color=brightgreen&left_text=Downloads)](https://pepy.tech/project/stremio)

A Python framework for building Stremio addons with async support, leveraging [BlackSheep](https://www.neoteroi.dev/blacksheep/) for fast HTTP handling and modern tooling.

## Features ✨

- **Async-first**: Leverage Python's `asyncio` for high-performance addons.
- **Decorator-based handlers**: Easily register handlers for resources like `stream`, `meta`, `catalog`, and `subtitles`.
- **Static file serving**: Serve static directories with custom cache control.
- **Central registry publishing**: Publish your addon to Stremio's central API with one call.

## Installation

```bash
pip install stremio
```

---

## Quick Start

```python
from stremio import Addon

# Define your addon manifest.
# See: https://github.com/Stremio/stremio-addon-sdk/blob/master/docs/api/responses/manifest.md
manifest = {
    "id": "org.example.myaddon",
    "version": "1.0.0",
    "name": "My Awesome Addon",
    "description": "This is a simple Awesome Addon!",
    "logo": "https://myaddon.com/logo.png",
    "catalogs": [],
    "resources": ["stream", "meta"],  # Add your supported resources here
    "types": ["movie"]
}

addon = Addon(manifest=manifest, port=7000)

# Add a stream handler
@addon.stream()
async def stream_handler(data):
    return {
        "streams": [{"name": "4K", "url": "https://example.com/cars_3.mp4"}]
    }

# Add a subtitles handler
@addon.subtitles()
async def subtitles_handler(data):
    return {
        "subtitles": [{"id": "1", "url": "https://example.com/cars_3_ar.srt", "lang": "Arabic"}]
    }

if __name__ == "__main__":
    addon.run()
```

---

## Usage Guide

### 1. Initialize the Addon

```python
addon = Addon(
    manifest=manifest,
    static_dir=["static"],  # Serve static files from these directories
    cache_max_age=3600,     # Cache responses for 1 hour; you can override this on handler response
    public_host="myaddon.com",
    log_level="info"
)
```

| Parameter       | Description                                                                            |
| --------------- | -------------------------------------------------------------------------------------- |
| `manifest`      | **Required** Addon manifest (validated on initialization).                             |
| `static_dir`    | Directories to serve static files from.                                                |
| `cache_max_age` | Max cache age in seconds for responses (default: `0`).                                 |
| `public_host`   | Public URL for addon installation links (e.g., `stremio://myaddon.com/manifest.json`). |
| `log_level`     | Server log level (`debug`, `info`, `warning`, `error`, `critical`).                    |

### 2. Register Resource Handlers

Use decorators to register handlers:

#### Stream Handler

```python
@addon.stream()
async def stream_handler(data):
    # data = {"id": "tt12345", "type": "movie", "extraArgs": None}
    return {"streams": [...]}  # See: https://github.com/Stremio/stremio-addon-sdk/blob/master/docs/api/responses/stream.md
```

#### Meta Handler

```python
@addon.meta()
async def meta_handler(data):
    return {"meta": {...}}  # See: https://github.com/Stremio/stremio-addon-sdk/blob/master/docs/api/responses/meta.md
```

#### Catalog Handler

```python
@addon.catalog()
async def catalog_handler(data):
    return {"metas": [...]}  # Return list of meta items. See: https://github.com/Stremio/stremio-addon-sdk/blob/master/docs/api/requests/defineCatalogHandler.md#returns
```

#### Subtitles Handler

```python
@addon.subtitles()
async def subtitles_handler(data):
    return {"subtitles": [...]}  # See: https://github.com/Stremio/stremio-addon-sdk/blob/master/docs/api/responses/subtitles.md
```

### 3. Custom Landing Page

```python
@addon.landing_page()
async def landing_page(request): # homepage a.k.a accessing myaddon.com/
    return "<h1>Welcome to My Addon!</h1>"
```

### 4. Publish to Central Registry

```python
async def publish_addon():
    await addon.publishToCentral(
        manifest_url="https://myaddon.com/manifest.json",
    )
```

---

## Advanced Configuration

### Cache Control

Return these keys in your handler responses to set cache headers:

```python
{
    "cacheMaxAge": 3600,          # max-age=3600
    "staleRevalidate": 86400,     # stale-while-revalidate=86400
    "staleError": 172800          # stale-if-error=172800
}
```

### Static Files

```python
Addon(static_dir=["assets", "public"])
```

Files in `assets/file.txt` will be available at `myaddon.com/assets/file.txt`.

---

<a name="license"></a>

## License

This project is licensed under the [MIT License](LICENSE).
