import fetchfox_sdk
from pprint import pprint

fox = fetchfox_sdk.FetchFox(quiet=True)

top_posts = \
    fox.extract(
        "https://news.ycombinator.com",
        {"url": "Find me all the URLs of the comments pages."
                "They'll all look like https://news.ycombinator.com/item?id=$SOMETHING"
        },
        limit=10)
# top_posts is a workflow.
# It will not be executed until the results are needed

# Here, we'll take a look at what was retrieved:
print("Found Post URLs:")
for post in top_posts:
    print(f"  {post.url}")

# top_posts is now carrying those results with it.

# We can derive multiple workflows from top_posts, and
# now they'll all inherit the results we already have.

####
# First workflow derived from top_posts:
####

user_urls_for_posters_of_top_ten_posts = \
    top_posts.extract(
        {"url": "The link to the profile of the user who submitted this post."
                "The URL will look like https://news.ycombinator.com/user?id=$USERNAME."
                "ONLY include URL for the post's author."
                "Do not include profiles for any commenters."},
        mode='single')

# This is the information we want to extract for each of the posters:
poster_info_template = {
    "username": "What is the username of this user?",
    "karma_points": "What is the number of 'karma' points this user has?",
    "created_date": "What is the 'created' date for this user?"
}

poster_infos = \
    user_urls_for_posters_of_top_ten_posts.extract(
        poster_info_template,
        mode='single')

####
# Second workflow derived from top_posts:
####

# A post can either be a link, or have a textual body.
links_and_usernames_from_top_ten_posts = \
    top_posts.extract({
        "url": "If the main content of the post is an external link to an article"
               "provide it here.  If the post is a text post (which has it's own"
               "content and NO external link), simply provide the post URL.",
        "username": "The username of the poster."
        },
        mode='single')

summaries_of_post_content = \
    links_and_usernames_from_top_ten_posts.extract({
        "content_summary":
            "Briefly summarize the main content of the article."
            "Ignore all comments and extra information."
            "There is only one article or post."
        },
        mode="single")

print("\n")

print("#####")
print("Posters info:")
print('#####')
print("")
for poster_info in poster_infos:
    pprint(dict(poster_info))

print("#####")
print("Summaries:")
print("#####")
print("")
for summary in summaries_of_post_content:
    pprint(dict(summary))