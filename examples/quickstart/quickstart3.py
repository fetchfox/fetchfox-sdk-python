import fetchfox_sdk
fox = fetchfox_sdk.FetchFox()

# We can extract multiple items from a page too:

# <<<QS_INCLUDE_START>>>
items = fox \
    .extract(
        "https://github.com/torvalds/linux/commits/master/",
        {
            "url": "What is the link to the commit?"
        },
        per_page="many",
        limit=10) \
    .extract(
        {
            "username": "Who committed this commit?",
            "url": "Link to the committing user. Looks like github.com/$USERNAME"
        },
        per_page='one') \
    .unique(['url']) \
    .extract(
        {
            "follower_count": "How many followers does the user have?"
        },
        per_page='one')

# This one takes a bit longer, since more pages are being loaded.
for item in items:
    print(f"  {item.username} has {item.follower_count} followers")
# <<<QS_INCLUDE_END>>>
