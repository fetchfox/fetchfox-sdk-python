import fetchfox_sdk
from pprint import pprint

fox = fetchfox_sdk.FetchFoxSDK()

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

workflow = (
    fox.workflow(product_list_url)
    .extract(find_urls_template, limit=20)
    .extract(bike_for_sale_template)
    .filter(filter_instructions)
)

result_items = workflow.results
pprint(result_items)