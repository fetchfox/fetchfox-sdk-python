import fetchfox_sdk
fox = fetchfox_sdk.FetchFox()

# We can extract multiple items from a page too:

# <<<QS_INCLUDE_START>>>
items = \
    fox.extract(
        "https://github.com/torvalds/linux/commits/master/",
        {
            "title": "What is the title of the commit?",
            "sha": "What is the hash of the commit?",
        },
        mode="multiple")

# This may take ~15 seconds before showing results.
print("Recent Commits:")
for item in items.limit(10):
    print(f"  {item.title}")
    print(f"  {item.sha}\n")

# <<<QS_INCLUDE_END>>>