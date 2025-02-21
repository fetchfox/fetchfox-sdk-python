import fetchfox_sdk
from pprint import pprint
import logging

fox = fetchfox_sdk.FetchFoxSDK()

city_pages = fox \
    .workflow("https://locations.traderjoes.com/pa/") \
    .extract(
        item_template = {
            "url": "Find me all the URLs for the city directories"
        }
    )

# City pages is a workflow.  It will not be executed until the results are
# needed somewhere.  When they are needed, that operation will block until
# they are ready.

store_item_template = {
    "store_address": "find me the address of the store",
    "store_number": "Find me the number of the store (it's in parentheses)",
    "store_phone": "Find me the phone number of the store"
}

store_info = city_pages.extract(item_template=store_item_template)

# store_info is a workflow that extends city_pages.  Since this extension
# does not depend on any results having been obtained already, no execution
# will occur yet.


# here, we'll directly trigger execution.

list_of_city_pages = list(city_pages)
#That yields:
#  list_of_city_pages = [
#     {'url': 'https://locations.traderjoes.com/pa/ardmore/'},
#     {'url': 'https://locations.traderjoes.com/pa/berwyn/'},
#     {'url': 'https://locations.traderjoes.com/pa/camp-hill/'},
#     {'url': 'https://locations.traderjoes.com/pa/jenkintown/'},
#     {'url': 'https://locations.traderjoes.com/pa/king-of-prussia/'},
#     {'url': 'https://locations.traderjoes.com/pa/media/'},
#     {'url': 'https://locations.traderjoes.com/pa/north-wales/'},
#     {'url': 'https://locations.traderjoes.com/pa/philadelphia/'},
#     {'url': 'https://locations.traderjoes.com/pa/pittsburgh/'},
#     {'url': 'https://locations.traderjoes.com/pa/state-college/'}
# ]
# AND
# city_pages is now carrying results with it.

# So, then, when we do something like the below, we are extending a workflow
# that has results.
# In this case, the first step will not be re-executed.  Instead we will
# initialize an empty workflow (which carries the already-computed results)
# and extend *that* with this new step.
store_urls = city_pages.extract(
    item_template = {
        "url": "Find me the URLs of Store detail pages."
    }
)
# Now `store_urls` is a workflow which is seeded with those URLs that we
# also have stored in `list_of_city_pages`.
# When `store_urls` is executed, we will ONLY execute this new extraction
# step, and we will NOT re-do the initial query to get the city-page URLs.

# We can dump the results here.  Since city pages is already carrying
# results, that workflow will not be re-run.
# Since store_urls hasn't been executed yet, we will implicitly run it now
# and export the results.
city_pages.export("city_pages.csv", force_overwrite=True)
store_urls.export("stores.jsonl", force_overwrite=True)

# As of now, `store_info` has actually never executed.
# I want to try a different approach for getting the store details and
# compare those results to those from `store_info`

# In the below, we'll actually load the store detail pages, and then try to
# extract the same information from those pages as we did from the list pages

store_info_from_detail_pages = \
    store_urls.extract(
        item_template=store_item_template,
    )

# We'll sort the results so they're easy to compare

sorted_store_info = sorted(store_info, key=lambda x: x['store_number'])

sorted_store_info2 = \
    sorted(store_info_from_detail_pages, key=lambda x: x['store_number'])

# Note that the above triggers execution of the workflows

assert len(sorted_store_info) == len(sorted_store_info2)
for i in range(len(sorted_store_info)):
    store_from_city_page = sorted_store_info[i]
    store_from_store_page = sorted_store_info2[i]

    if store_from_city_page != store_from_store_page:
        print(f"Difference found for store_number {store_from_city_page['store_number']}:")

        # Print differences field by field
        for key in store_from_city_page.keys():
            if store_from_city_page[key] != store_from_store_page.get(key):
                print(f"  {key}:")
                print(f"    store from city page: {store_from_city_page[key]}")
                print(f"    Store from store page: {store_from_store_page.get(key)}")

        print("-" * 50)  # Separator for readability
