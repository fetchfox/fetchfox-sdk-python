import fetchfox_sdk
from pprint import pprint

fox = fetchfox_sdk.FetchFoxSDK()

STATUS_URL = "https://status.openai.com/"

convenient_results = \
    fox.just_extract(
        STATUS_URL,
        instruction="Get me a list of incidents, the time they began investigating, and the time they were resolved."
    )

print("Ran convenience extract with prompt only:")
pprint(convenient_results)

# On the first run, I get results like this:
# {
#     "description": "ChatGPT issues connecting Voice on Web",
#     "investigation_begin_time": "Feb 04, 2025 - 11:02 PST",
#     "resolution_time": "Feb 04, 2025 - 11:53 PST",
#     "url": "https://status.openai.com/incidents/2w5bb7g12f92"
# }

# On the second run, I get results like this:
# {
#     "investigation_begin": "2025-02-12 02:35 PST",
#     "resolved_time": "2025-02-12 05:12 PST",
#     "title": "Elevated Subscription Loading Errors",
#     "url": "https://status.openai.com/incidents/2ggy1dxx8z8c"
# }

# It's great that we're able to extract the required information from just
# a prompt!

# It would be helpful to constrain the output format into something consistent
# So let's describe the item format we want (in example #2)