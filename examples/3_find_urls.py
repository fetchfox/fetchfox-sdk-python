import fetchfox_sdk
from pprint import pprint

fox = fetchfox_sdk.FetchFoxSDK()

# product_list_url = "https://www.ebay.com/sch/i.html?_nkw=cool+sneaks"

# # Here we'll find the URLs to the products listed on this page.
# # You might to do this to build our own pipeline locally.

# # If, for example,  you just want to an extraction on each one of these URLS
# # though, Fetchfox can manage the execution of that workflow too!
# # See the next example.

# urls = \
#     fox.find_urls(
#         product_list_url,
#         instruction="Find me the links for each product detail page."
#         			"Only include those that are offering free delivery."
#     )

# print("Ran find_urls:")
# pprint(urls)

urls = \
    fox.find_urls(
        "https://www.bicyclebluebook.com/marketplace/buy-now/",
        instruction="Find me the links for each product detail page."
    )

print("Ran find_urls:")
pprint(urls)