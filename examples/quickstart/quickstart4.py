import fetchfox_sdk
fox = fetchfox_sdk.FetchFox()

# <<<QS_INCLUDE_START>>>
items = \
    fox.extract(
        "https://github.com/torvalds/linux/commits/master/",
        {
            "title": "What is the title of the commit?",
            "sha": "What is the hash of the commit?",
        },
        mode="multiple",
        max_pages=5) \
    .filter("Only show me commits that pertain to networking.") \
    .limit(10)

items.export("networking_commits.jsonl", overwrite=True)
# <<<QS_INCLUDE_END>>>

print("Recent Networking Commits:")
for item in items:
    print(f"  {item.title}")
