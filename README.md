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

# MARCELL COMMENTS:
# - I changed it to a working URL so people will be able to copy/paste this in
# - Added a limit of 10 so they don't accidently scrape a thousand items
# - First argument is an extraction target, which for now is always a URL or list of URLs
# - Second argument is the item template
# - Extra options can be passed in as kwargs
# - item_set is class `ItemSet`
# - Removed instruction mode. It's lower LoC and lower complexity for us to have just 1 way to do it

# Important:
# - item_set is lazy eval, and so fox.extract() evaluates instantly
# - There is no distinction between workflows and fox.extract(), except the argument order (see below)

# You can do these things to get evaluate the ItemSet:

# get them all
items = list(item_set)

# get them as they come in
for item in item_set:
    # item is class `Item`, fields can be accessed as below. Similar behavior to how DB rows are returned by a django query set
    print(item)
    print(item.name)
    print(item.number)
    print(item.url)

# MARCELL COMMENTS:
# - The default example should to the `for item in item_set` mode, so that the developer quickly sees the first result. We don't want them to wait for 10 items, which could take a minute. They should see the first result ASAP

# And now you can do the next step

item_set_2 = item_set.extract({
    "review_author": "Who is the author of this review",
    "review_rating": "The X.X/5 rating",
}, follow="product_url")


```

The above is just a simple way to get started.  You can also build workflows
out of chains of operations, and even compose them together!

```python
posts = fox.extract(
    "https://www.reddit.com/r/Ultralight/top/?t=day",
    {
        "post_title": "What is the title of the post",
        "num_comments": "How many comments does the post have?",
        "url": "What is the URL of the post?"
    },
    limit=10)

# Workflows are always executed completely, but lazily.

# If you extend a workflow that has not executed, you're just adding steps
# that will be performed later:

# MARCELL COMMENT: nit, but should we try to make all these fit on one line?

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

# MARCELL COMMENTS: This is cool

sleeping_gear_posts = todays_posts.filter(filter_for_sleeping_gear)
down_posts = todays_posts.filter(filter_for_down) #If not used, this won't run

# Maybe we want to find all the comments from the posts about sleeping gear:

comment_item_template = {
    "comment_body": "The full text of the comment",
    "comment_sentiment":
        "Rate the comment's mood.  Choose either 'very negative',"
        " 'slightly negative', 'neutral', 'slightly positive', or 'very positive'."
}

# MARCELL COMMENT: At some point, either here or earlier, we should talk about `url` field follows. Probably it should be a kwarg, so by default `url` field is followed, but you can change it

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
