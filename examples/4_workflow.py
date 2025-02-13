import fetchfox_sdk
from pprint import pprint

fox = fetchfox_sdk.FetchFoxSDK()

product_list_url = \
    "https://www.bicyclebluebook.com/marketplace/buy-now/?viewport=desktop&ss=Front&page=1&bt=Disc+-+Hydraulic&storeId=&sn=&sell_type=ALL&lt=BIKE&c=USED&w=26%22"

find_urls_instructions = \
    "Find me the links to each detail page for a bicycle for sale."

bike_for_sale_template = {
    "full_description": "The seller's entire textual description.",
    "frame_size": "The size of the bicyle frame.",
    "price": "The price the seller is asking for the bike.",
    "MSRP": "The original MSRP price of the bike as given by this listing, or (not found) if there is not one provided."
}

filter_instructions = "Exclude any listings where the description includes phrases such as 'no tire kickers' or 'i know what i have' or 'serious buyers only' or 'no lowballers' or anything else that suggests an unwillingness to negotiate."

workflow = (
    fetchfox_sdk.Workflow()
    .init(product_list_url)
    .find_urls(find_urls_instructions, limit=10)
    .extract(bike_for_sale_template)
    .filter(filter_instructions)
)

workflow_id = fox.register_workflow(workflow)
job_id = fox.run_workflow(workflow_id=workflow_id)
result_items = fox.await_job_completion(job_id)
pprint(result_items)