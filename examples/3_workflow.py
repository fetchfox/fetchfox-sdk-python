import fetchfox_sdk

fox = fetchfox_sdk.FetchFox()

# Fetchfox can run complex workflows.

# Let's visit a page listing bikes for sale, and get URLs to individual bikes
bikes_detail_page_urls = \
    fox.extract(
        "https://www.bicyclebluebook.com/marketplace/buy-now",
        {"url": "Find me the links to each detail page for a bicycle for sale."},
        limit=20)
# The above will yield items like: {"url": "$URL_TO_A_BIKE"}

# IMPORTANT: When a "url" field is present in the items, Fetchfox will follow
# that URL in the next step.

# Now we will extract information from the individual bicycle detail pages:
bikes_for_sale = \
    bikes_detail_page_urls.extract({
        "full_description": "Find the seller's entire textual description.",
        "frame_size": "Find the size of the bicyle frame.",
        "price": "What price is the seller asking for the bike?",
        "MSRP": "What is the original MSRP price of the bike, as given here?"})

# We can filter those result items using natural language:
negotiable_bikes = \
    bikes_for_sale.filter(
        "Exclude any items where the seller indiciates unwillingness to "
        "negotiate on price.")

# Workflows are lazy, so nothing is run until the result items are needed here:
for bike in negotiable_bikes:
    print(f"{bike}")

# Now, those results are cached on `filtered_bikes`, so we can use them again
# without re-running the job:
all_bikes = list(negotiable_bikes)
first_bike = negotiable_bikes[0]

# We can also export the results to CSV or JSONL files:
negotiable_bikes.export("bikes.jsonl", overwrite=True)
negotiable_bikes.export("bikes.csv", overwrite=True)

# You can also write all of the above as a single chain like this:
# fox\
# .extract(
#     "https://www.bicyclebluebook.com/marketplace/buy-now",
#     {"url": "Find me the links to each detail page for a bicycle for sale."},
#     limit=20) \
# .extract({
#     "full_description": "Find the seller's entire textual description.",
#     "frame_size": "Find the size of the bicyle frame.",
#     "price": "What price is the seller asking for the bike?",
#     "MSRP": "What is the original MSRP price of the bike, as given here?"}) \
# .filter(
#     "Exclude any items where the seller indiciates unwillingness to "
#     "negotiate on price.") \
# .export("bikes.jsonl", overwrite=True) \
# .export("bikes.csv", overwrite=True)
