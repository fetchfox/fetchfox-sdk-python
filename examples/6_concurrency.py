import fetchfox_sdk
from pprint import pprint
import concurrent.futures

fox = fetchfox_sdk.FetchFox(quiet=True)

# When you run a workflow, we handle concurrent execution of your requests
# on the backend.

# You can also run multiple workflows concurrently with the Python SDK.
# <<<QS_INCLUDE_START1>>>
top_posts_on_hn = \
    fox.extract(
        "https://news.ycombinator.com",
        {"title": "Find me all the titles of the posts."},
        limit=10)

top_posts_on_reddit = \
    fox.extract(
        "https://old.reddit.com",
        {"title": "Find me all the titles of the posts."},
        limit=10)

top_posts_on_slashdot = \
    fox.extract(
        "https://news.slashdot.org/",
        {"title": "Find me all the titles of the posts."},
        limit=10)

# The easiest way to run workflows concurrently is to use futures:

top_posts_on_hn_future = top_posts_on_hn.results_future()
top_posts_on_reddit_future = top_posts_on_reddit.results_future()
top_posts_on_slashdot_future = top_posts_on_slashdot.results_future()
# The above will run all 3 workflows.
# These variables hold standard Python concurrent.futures.Futures

# If you don't want to do anything until all of them are finished, you can
# simply collect the results by using .result() on the futures.
# This will block until they all finish.

hn_posts_results = top_posts_on_hn_future.result()
reddit_posts_results = top_posts_on_reddit_future.result()
slashdot_posts_results = top_posts_on_slashdot_future.result()
# The futures resolve directly to a list of result items.

print(hn_posts_results[0])

# After those futures complete, the results are *also* available
# via the workflows, which may be used normally.

print(top_posts_on_hn[1])
# <<<QS_INCLUDE_END1>>>


print("######################################################################")
print("######################################################################")

# Alternatively, you might want to start processing results as soon as
# the first batch of results becomes available.
# You can do this using concurrent.futures.as_completed(), as below:

workflows = []

workflows.append(
    fox.extract(
        "https://news.ycombinator.com",
        {"title": "Find me all the titles of the posts."},
        limit=10)
    )

workflows.append(
    fox.extract(
        "https://old.reddit.com",
        {"title": "Find me all the titles of the posts."},
        limit=10)
    )

workflows.append(
    fox.extract(
        "https://news.slashdot.org/",
        {"title": "Find me all the titles of the posts."},
        limit=10)
    )

futures = [ workflow.results_future() for workflow in workflows ]

for completed_future in concurrent.futures.as_completed(futures):
    for result_item in completed_future.result():
        print("Found Post:")
        print(f"  {result_item.title}")
        print(f"    on")
        print(f"  {result_item._url}")
        print("")

print("######################################################################")
print("######################################################################")

# Because these are standard Python concurrent.futures.Futures, you can also
# attach one or more callbacks to them:

top_posts_on_slashdot = \
    fox.extract(
        "https://news.slashdot.org/",
        {"title": "Find me all the titles of the posts."},
        limit=10)

top_posts_on_slashdot_future = top_posts_on_slashdot.results_future()

def handle_slashdot_posts(future):
    print("Here's a slashdot post: ")
    print(f"   {future.result()[0]}")
    # The results are also saved onto the workflow before this callback,
    # so you could do something like this too:
    top_posts_on_slashdot.export("slashdot_top_posts.jsonl", overwrite=True)

top_posts_on_slashdot_future.add_done_callback(handle_slashdot_posts)