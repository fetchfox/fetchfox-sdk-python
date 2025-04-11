import fetchfox_sdk
fox = fetchfox_sdk.FetchFox()

# We can extract multiple items from a page too:

items = \# <<<QS_INCLUDE_START>>>
    fox.extract(
        "https://github.com/torvalds/linux/commits/master/",
        {
            "title": "What is the title of the commit?",
            "sha": "What is the hash of the commit?",
        },
        per_page="many",
        max_pages=5)
# <<<QS_INCLUDE_END>>>

# This may take ~15 seconds before showing results.
print("Recent Commits:")
for item in items:
    print(f"  {item.title}")
    print(f"  {item.sha}\n")
