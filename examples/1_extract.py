import fetchfox_sdk

fox = fetchfox_sdk.FetchFox()

STATUS_URL = "https://status.anthropic.com/"

# Here we'll provide a template to extract items.
# "Impact Level" is actually only presented as a variation in the coloring, but
# we can still extract this information.

incident_item_template = {
    "title":
        "Get the title of the incident",
    "investigation_start_time":
        "Find the timestamp when 'investigating' was posted for that incident.",
    'resolution_time':
        "Find the timestamp when 'resolved' was posted for that incident."
}

incidents = fox.extract(STATUS_URL, incident_item_template, per_page='many')

# This may take ~30 seconds to show results
for incident in incidents:
    print(f"  {incident}")
