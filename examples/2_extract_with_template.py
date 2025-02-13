import fetchfox_sdk
from pprint import pprint

fox = fetchfox_sdk.FetchFoxSDK()

STATUS_URL = "https://status.openai.com/"

# Here we'll provide a template, and ask for another field.
# "Impact Level" is actually only presented as a variation in the coloring, but
# we can still extract this information.

incident_item_template = {
    "title":
        "Get the title of the incident",
    "investigation_start_time":
        "Find the timestamp when 'investigating' was posted for that incident.",
    'resolution_time':
        "Find the timestamp when 'resolved' was posted for that incident.",
    'impact_level':
        "The incident title has an html class that describes the impact level."
        "Please provide the impact level for the incident here."
    #"impact_level": "What is the severity of the incident?"
}

# NOTE: impact-level is hit or miss with the simpler prompting.
# may be more reliable with the better instruction, but impressive that it
# gets it sometimes anyway.

consistent_results = \
    fox.extract(
        STATUS_URL,
        item_template=incident_item_template
    )

print("Ran extract with template:")
pprint(consistent_results)