import fetchfox_sdk
from pprint import pprint
import queue
import time

fox = fetchfox_sdk.FetchFox()

# It's also possible to get callbacks on a per-item basis.

city_pages = \
    fox.extract(
        "https://locations.traderjoes.com/pa/",
        { "url": "Find me all the URLs for the city directories" }
)

result_queue = queue.Queue()

def on_tj_city_url(item):
    result_queue.put(item)

def on_exception(exception):
    result_queue.put(exception)

city_pages.run_with_callback_for_result_items(on_tj_city_url, on_exception)

while city_pages.callback_thread_is_running():
    try:
        item = result_queue.get(timeout=0.1)
        print(f"Got Store URL: {item.url}")
    except queue.Empty:
        pass

    time.sleep(0.1)

city_pages.wait_until_done()

# At this point, after your callbacks have been executed, city_pages
# is carrying the results and you can use them again:

city_pages.export("/tmp/city_pages.csv", overwrite=True)
