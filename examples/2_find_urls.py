import fetchfox_sdk

fox = fetchfox_sdk.FetchFox()

# Here we'll find the URLs to the products listed on this page.
# You might to do this to build your own pipeline locally.

# If, for example,  you just want to an extraction on each one of these URLS
# though, Fetchfox can manage the execution of that workflow too!
# See the next example.

ebay_items = \
    fox.extract(
        "https://www.ebay.com/sch/i.html?_nkw=cool+sneaks",
        {
            "url":  "Find me the links for each product detail page."
                    "Only include those that are offering free delivery."
        })

# Do something else or extend your workflow here, it won't run
# until the results are used somewhere.

for ebay_item in ebay_items.limit(10):
    print(f"Found: {ebay_item.url}")