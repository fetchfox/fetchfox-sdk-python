import fetchfox_sdk

fox = fetchfox_sdk.FetchFox()

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
}

incidents = fox.extract(STATUS_URL, incident_item_template)

for incident in incidents:
    print(f"  {incident}")
