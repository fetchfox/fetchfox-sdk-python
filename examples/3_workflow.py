import fetchfox_sdk
from pprint import pprint

fox = fetchfox_sdk.FetchFox()

product_list_url = \
    "https://www.bicyclebluebook.com/marketplace/buy-now/?viewport=desktop&ss=Front&page=1&bt=Disc+-+Hydraulic&storeId=&sn=&sell_type=ALL&lt=BIKE&c=USED&w=26%22"

find_urls_template = {
    "url": "Find me the links to each detail page for a bicycle for sale."
}

bike_for_sale_template = {
    "full_description": "Find the seller's entire textual description.",
    "frame_size": "Find the size of the bicyle frame.",
    "price": "What price is the seller asking for the bike?",
    "MSRP": "What is the original MSRP price of the bike as given by this listing, or (not found) if there is not one provided."
}

filter_instructions = "Exclude any listings where the description includes phrases such as 'no tire kickers' or 'i know what i have' or 'serious buyers only' or 'no lowballers' or anything else that suggests an unwillingness to negotiate."

import pdb
pdb.set_trace()
bikes_detail_pages = fox.extract(product_list_url, find_urls_template, limit=20)

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
