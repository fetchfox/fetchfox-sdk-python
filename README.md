# FetchFox SDK
Python library for the Fetchfox API.

FetchFox uses AI to power flexible scraping workflows.

## Installation

### From GitHub
```bash
pip install git+https://github.com/yourusername/fetchfox-sdk.git
```

### From local directory
```bash
pip install .
```

### From zip file
```bash
pip install fetchfox_sdk-0.1.0.zip
```

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
urls = fox.crawl(
    url="https://example.com",
    instruction="Find all product detail pages"
)
```