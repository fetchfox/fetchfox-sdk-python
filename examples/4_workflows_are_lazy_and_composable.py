import fetchfox_sdk
from pprint import pprint
import logging

fox = fetchfox_sdk.FetchFox()

city_pages = \
	fox.extract(
    	"https://locations.traderjoes.com/pa/",
    	{"url": "Find me all the URLs for the city directories"}
    )
# City pages is a workflow.  It will not be executed until the results are
# needed somewhere.

# Here, we'll directly trigger execution and take a look at some intermediate
# results:
list_of_city_pages = list(city_pages)

# That yields:
#  list_of_city_pages = [
#     {'url': 'https://locations.traderjoes.com/pa/ardmore/'},
#     {'url': 'https://locations.traderjoes.com/pa/berwyn/'},
#	  <...>
#  ]

# city_pages is now carrying those results with it.

# We can derive multiple workflows from the one that already has results now.

# Let's try two different ways of extracting the same type of item.
# We want items like this:
store_item_template = {
    "store_address": "find me the address of the store",
    "store_number": "Find me the number of the store (it's in parentheses)",
    "store_phone": "Find me the phone number of the store"
}

store_url_template = {
	"url": "The URLs of the store detail pages, for each individual store."
}


#TJ is the wrong example.
# We want to demonstrate, in particular, branching a workflow to extract two
# different types of mutually exclusive things from the same results.
# Maybe "top ten posts", but in one flow we follow the username links to their profiles
# and find their karma, but in another flow we follow the post URLs to get something


# The first thing we'll do is extract store_items directly from the
# city index pages:
store_info = city_pages.extract(store_item_template)

# The other thing we'll try is
store_urls = city_pages.extract({"url": "The URLs of Store detail pages."})
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
