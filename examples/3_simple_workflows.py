import fetchfox_sdk

fox = fetchfox_sdk.FetchFox()

# Fetchfox can run workflows, which are sequences of steps.

# The first and most powerful workflow feature you should know about is that
#Fetchfox can follow URLs, loading those pages for the next steps.

some_articles = \
    fox.extract(
        "https://substack.com/browse/staff-picks",
        {
            "url":
                "The links to articles.  These will usually look like "
                "https://$SOMETHING.substack.com/p/$SOME_TITLE_WORDS"
        },
        limit=10)
# The above will yield article URLs like:
#   https://theannaedit.substack.com/p/how-to-be-organised-in-2025?[...]

# Now, we will add another extraction step.
# Because those result items have a "url" field, each of them will be loaded.

# Our next "extract" step will be operating on those URLs we just found.
# (The articles themselves, rather than the initial list of articles)

article_summaries = \
    some_articles.extract(
        {
            "article_title": "The title of the article.",
            "posted_date": "The date the article was posted.",
            "author_name": "The name of the author of the article",
            "article_summary": "A summary of the main content of the article."
                               "Provide 50-100 words."
        },
        per_page="one")

# This may take ~30 seconds to show results.
print("Found Articles:")
for result in article_summaries:
    print(f"  {result.article_title} by {result.author_name}:")
    print(f"    {result.article_summary}\n")