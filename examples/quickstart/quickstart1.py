import fetchfox_sdk
fox = fetchfox_sdk.FetchFox()

# Here we'll extract some data from a page:
items = \
    fox.extract(
        "https://github.com/torvalds/linux",
        {
            "forks": "How many forks does this repository have?",
            "stars": "How many stars does this repository have?",
            "name": "What is the full name of the repository?"
        },
        per_page='one')

# This may take 15 seconds or so.
print(items[0])