import fetchfox_sdk

fox = fetchfox_sdk.FetchFox()

# This is a page with a list of bikes for sale, each bike is a link:
product_list_url = \
    "https://www.bicyclebluebook.com/marketplace/buy-now/?viewport=desktop&ss=Front&page=1&bt=Disc+-+Hydraulic&storeId=&sn=&sell_type=ALL&lt=BIKE&c=USED&w=26%22"

# We want to extract the URLs that point to individual bikes, so we'll use this:
find_urls_template = {
    "url": "Find me the links to each detail page for a bicycle for sale."
}

# We will extract information from the bike-page, using this format:
bike_for_sale_template = {
    "full_description": "Find the seller's entire textual description.",
    "frame_size": "Find the size of the bicyle frame.",
    "price": "What price is the seller asking for the bike?",
    "MSRP": "What is the original MSRP price of the bike as given by this listing, or (not found) if there is not one provided."
}

# We will use an AI-powered natural language filter to remove some bikes:
filter_instructions = "Exclude any listings where the description includes phrases such as 'no tire kickers' or 'i know what i have' or 'serious buyers only' or 'no lowballers' or anything else that suggests an unwillingness to negotiate."

# Let's get 20 bike pages from the list page:
bikes_detail_pages = fox.extract(product_list_url, find_urls_template, limit=20)

# Now we extract the bike_for_sale items, and filter them
filtered_bikes = (
    bikes_detail_pages
    .extract(bike_for_sale_template)
    .filter(filter_instructions)
)

# Workflows are lazy, so nothing is run until the result items are needed here:
for bike in filtered_bikes:
    print(f"{bike}")

# Now, those results are cached on `filtered_bikes`, so we can use them again
# without re-running the job:
all_bikes = list(filtered_bikes)
first_bike = filtered_bikes[0]

# We can also export the results to CSV or JSONL files:
filtered_bikes.export("bikes.jsonl", overwrite=True)
filtered_bikes.export("bikes.csv", overwrite=True)
