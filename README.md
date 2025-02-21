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
fox = FetchFoxSDK(api_key="YOUR_API_KEY") # Initialize the client
# or, the API key may be provided in the environment variable: FETCHFOX_API_KEY
```

Fetchfox can intelligently extract data from webpages.  If you want to see what
Fetchfox can do, try running an extraction similar to one of these examples on any webpage.

```python
# Extract data from a webpage
results = fox.just_extract(
    url="https://example.com/products-list",
    instruction="Extract all product prices"
)

# or, to control the output item format:
results = fox.just_extract(
    url = "https://example.com/products-list",
    item_template={
        "product_name": "What is the name of the product?",
        "product_price": "What is the price of this product?",
        "product_rating": "What is the rating (in stars) of this product?"
    }
)

# You can find URLs too, if you want to identify more pages to extract from.
urls = fox.just_extract(
    url="https://example.com/products-list",
    item_template={
        "url": "Find me the URLs of all the products that include free shipping."
    }
)

```

The above is just a simple way to get started.  You can also build workflows
out of chains of operations, and even compose them together!

```python
post_item_template = {
    "post_title": "What is the title of the post",
    "num_comments": "How many comments does the post have?",
    "url": "What is the URL of the post?"
}

todays_posts = (
    fox.workflow("https://www.reddit.com/r/Ultralight/top/?t=day")
    .extract(post_item_template)
)

# Workflows are always executed completely, but lazily.

# If you extend a workflow that has not executed, you're just adding steps
# that will be performed later:

trails_posts = todays_posts.filter(
    "Only show me posts that are about trails, skip those marked 'gear review'"
    "or 'purchase advice'.")

# If we do something like the below, we'll execute `todays_posts`
print("Todays Posts:")
for post in todays_posts:
    print(post['title'])

# Now, when we derive workflows from one that has results, they will be
# seeded with those results as a starting point, so 'todays_posts' only runs once:

filter_for_sleeping_gear = (
    "Please include only posts which pertain to sleeping gear"
    "such as pads, bags, quilts, and pillows."
)

filter_for_down = (
    "Please include only posts which pertain to down (goose, duck, or synthetic)."
    "Include any posts which mention 'fill-power' or 'puffy' or other wording "
    "that may tangentially relate to backpacking equipment made from down."
)

sleeping_gear_posts = todays_posts.filter(filter_for_sleeping_gear)
down_posts = todays_posts.filter(filter_for_down) #If not used, this won't run

# Maybe we want to find all the comments from the posts about sleeping gear:

comment_item_template = {
    "comment_body": "The full text of the comment",
    "comment_sentiment":
        "Rate the comment's mood.  Choose either 'very negative',"
        " 'slightly negative', 'neutral', 'slightly positive', or 'very positive'."
}

comments_from_sleeping_gear_posts = \
    sleeping_gear_posts.extract(item_template=comment_item_template)

comments_mentioning_a_brand_or_product = \
    comments_from_sleeping_gear_posts.filter(
        "Exclude all posts that do not mention a specific brand or product.")

# You can use the results here, or export to a JSONL or CSV file for analysis
comments_mentioning_a_brand_or_product.export(
    "comments_with_sentiment_and_references_to_specific_products.jsonl")

```

### Examples
Check out the `examples` folder for some typical usages.

[https://github.com/fetchfox/fetchfox-sdk-python/tree/main/examples](https://github.com/fetchfox/fetchfox-sdk-python/tree/main/examples)