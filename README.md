# FetchFox SDK
Python library for the Fetchfox API.

FetchFox uses AI to power flexible scraping workflows.

NOTE: This interface is currently subject to change as we respond to early feedback.

## Installation

### Via PyPI

`pip install fetchfox-sdk`

## Quick Start
```python
from fetchfox_sdk import FetchFox
fox = FetchFox(api_key="YOUR_API_KEY") # Initialize the client
# or, the API key may be provided in the environment variable: FETCHFOX_API_KEY
```

Fetchfox can intelligently extract data from webpages.  If you want to see what
Fetchfox can do, try running an extraction similar to one of these examples on any webpage.

```python
# Extract data from a webpage
item_set = fox.extract(
    "https://pokemondb.net/pokedex/national",
    {
        "name": "What is the name of the Pokemon?",
        "number": "What is the number of the Pokemon?",
        "url": "What is the url of the Pokemon?",
    },
    limit=10)

# This may take ~10-20 seconds
for item in item_set:
    print(item)
    print(item.name)
    print(item.number)
    print(item.url)

```

The above is just a simple way to get started.  You can also build workflows
out of chains of operations, and even compose them together!

```python
posts = fox.extract(
    "https://www.reddit.com/r/Ultralight/top/?t=day",
    {
        "title": "What is the title of the post",
        "num_comments": "How many comments does the post have?",
        "url": "What is the URL of the post?"
    },
    limit=10)

# Workflows are always executed completely, but lazily.

# If you extend a workflow that has not executed, you're just adding steps
# that will be performed later:

trails_posts = posts.filter(
    "Only show me posts about trails, skip those marked 'gear review'")

# If we do something like the below, we'll execute `posts`
# (this may take 30-40 seconds)
print("Todays Posts:")
for post in posts:
    print(f"  {post.title}")

# Now, when we derive workflows from one that has results, they will be
# seeded with those results as a starting point, so 'posts' only runs once:

filter_for_sleeping_gear = (
    "Please include only posts which pertain to sleeping gear"
    "such as pads, bags, quilts, and pillows."
)

filter_for_down = (
    "Please include only posts which pertain to down (goose, duck, or synthetic)."
    "Include any posts which mention 'fill-power' or 'puffy' or other wording "
    "that may tangentially relate to backpacking equipment made from down."
)

sleeping_gear_posts = posts.filter(filter_for_sleeping_gear)
down_posts = posts.filter(filter_for_down) #If not used, this won't run

# Maybe we want to find all the comments from the posts about sleeping gear:

comment_item_template = {
    "comment_body": "The full text of the comment",
    "comment_sentiment":
        "Rate the comment's mood.  Choose either 'very negative',"
        " 'slightly negative', 'neutral', 'slightly positive', or 'very positive'."
}

# One important thing to know is that the "url" field of a result item will be
# _followed_ in the next extraction step:

comments_from_sleeping_gear_posts = \
    sleeping_gear_posts.extract(
        comment_item_template,
        per_page='many')
# When the above runs, FetchFox will fetch each URL from the remaining
# items in `posts`

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