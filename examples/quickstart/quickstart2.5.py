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
            "url": "What is the link to the commit?" # Added this field
        },
        mode="multiple")
# Extracts URLs like: https://github.com/torvalds/linux/commit/f31529...
# <<<QS_INCLUDE_END>>>


# This may take ~15 seconds before showing results.
print("Recent Commits:")
for item in items.limit(10):
    print(f"  {item.url}\n")


# <<<QS_INCLUDE_START2>>>
items2 = \
    items.extract(  # Note that we're extending `items` from before.
        {
            "username": "Who committed this commit?",
            "summary": "Summarize the extended description briefly."
        },
        mode='single')
# <<<QS_INCLUDE_END2>>>

for commit_detail in items2:
    print(f"  {commit_detail.username}")
    print(f"  {commit_detail.summary}\n\n")
