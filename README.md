# FetchFox SDK
Python library for the Fetchfox API.

FetchFox uses AI to power flexible scraping workflows.

## Installation

### Into a Fresh Venv, for a new project
```bash
git clone git@github.com:hephaestus-klytotekhnes/fetchfox-sdk-python.git
cd fetchfox-sdk-python
python -m venv venv
source ./venv/bin/activate
pip install .

export FETCHFOX_API_KEY=$YOUR_KEY_HERE

# Try an example:
cd examples/
python 1_extract_with_prompt.py

```
### Via PyPI
Coming soon!

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