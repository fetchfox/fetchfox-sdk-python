import fetchfox_sdk
from pprint import pprint

fox = fetchfox_sdk.FetchFoxSDK()

STATUS_URL = "https://status.openai.com/"

incident_item_template = {
    "title": "Get the title of the incident",
    "investigation_start_time":  "Find the timestamp when 'investigating' was posted for that incident.",
    'resolution_time': "Find the timestamp when 'resolved' was posted for that incident.",
    'impact_level': "The incident title has an html class that describes the impact level.  Please provide the impact level for the incident here."
}

consistent_results = \
    fox.extract(
        STATUS_URL,
        item_template=incident_item_template
    )

print("Ran extract with template:")
pprint(consistent_results)

# Default behavior is to only extract one item from a given page.

# In this case, we want multiple items, so we use single=False.

#TODO: single=False should maybe be multiple=True?

more_results = \
    fox.extract(
        STATUS_URL,
        item_template=incident_item_template,
        single=False
    )

print("Ran extract with template:")
pprint(consistent_results)