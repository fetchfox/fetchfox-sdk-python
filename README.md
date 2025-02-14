# FetchFox SDK
Python library for the Fetchfox API.

FetchFox uses AI to power flexible scraping workflows.

NOTE: This interface is currently subject to change as we respond to early feedback.

## Installation

### Via PyPI

`pip install fetchfox-sdk`

## Quick Start
```python
from fetchfox_sdk import FetchFoxSDK

# Initialize the client
fox = FetchFoxSDK(api_key="YOUR_API_KEY")
# or, the API key may be provided in the environment variable: FETCHFOX_API_KEY

# Extract data from a webpage
results = fox.extract(
    url="https://example.com",
    instruction="Extract all product prices"
)

# Find specific URLs
urls = fox.find_urls(
    url="https://example.com",
    instruction="Find all product detail pages"
)

```

### Examples
Check out the `examples` folder for some typical usages.

[https://github.com/fetchfox/fetchfox-sdk-python/tree/main/examples](https://github.com/fetchfox/fetchfox-sdk-python/tree/main/examples)