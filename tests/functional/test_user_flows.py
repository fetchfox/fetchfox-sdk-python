import pytest
import os
import tempfile
import shutil
import json
import re

import fetchfox_sdk
from fetchfox_sdk import FetchFox

# Skip all tests if no API key is available
pytestmark = pytest.mark.skipif(
    os.environ.get("FETCHFOX_API_KEY") is None,
    reason="No FETCHFOX_API_KEY environment variable found"
)
# NOTE: This test module, for now, is just intended to run against prod

@pytest.fixture
def fox():
    """Create a FetchFox instance with quiet mode to reduce output noise."""
    return FetchFox()

@pytest.fixture
def temp_dir():
    """Create and manage a temporary directory for file exports."""
    dir_path = tempfile.mkdtemp()
    old_dir = os.getcwd()
    os.chdir(dir_path)
    
    yield dir_path
    
    # Cleanup after test
    os.chdir(old_dir)
    shutil.rmtree(dir_path)

def test_01_basic_extraction(fox):
    """Test basic extraction from a repo (quickstart1.py)."""
    # Basic repo information extraction
    items = fox.extract(
        "https://github.com/torvalds/linux",
        {
            "forks": "How many forks does this repository have?",
            "stars": "How many stars does this repository have?",
            "name": "What is the full name of the repository?"
        },
        per_page='one')
    
    # Access the result which will trigger execution
    result = items[0]
    
    # Basic assertions
    assert result is not None
    assert hasattr(result, 'forks')
    assert hasattr(result, 'stars')
    assert hasattr(result, 'name')
    
    # The name should be "torvalds/linux"
    assert result.name == "torvalds/linux"
    
    # Forks and stars should have numbers
    assert \
        re.search(r'\d', result.forks), \
        f"No digits found in forks: {result.forks}"

    assert \
        re.search(r'\d', result.stars), \
        f"No digits found in stars: {result.stars}"


def test_02_multiple_items_extraction(fox):
    """Test extracting multiple items (quickstart2.py)."""
    # Extract multiple commits
    items = fox.extract(
        "https://github.com/torvalds/linux/commits/master/",
        {
            "title": "What is the title of the commit?",
            "sha": "What is the hash of the commit?",
        },
        per_page='many')
    
    results = list(items.limit(3))
    
    # Basic assertions
    assert len(results) > 0, "Should have at least one result"
    assert len(results) <= 3, "Should have at most 3 results due to limit"
    
    for result in results:
        assert hasattr(result, 'title')
        assert hasattr(result, 'sha')
        # Title should not be empty
        assert len(result.title.strip()) > 0, "Title should not be empty"
        # SHA should look like a git hash (hexadecimal)
        assert re.match(r'^[0-9a-f]{7,40}$', result.sha.lower()), f"Invalid SHA: {result.sha}"

def test_03_follow_urls_workflow(fox):
    """Test following URLs in a workflow (quickstart2.5.py)."""
    # First extract commits with URLs
    items = fox.extract(
        "https://github.com/torvalds/linux/commits/master/",
        {
            "title": "What is the title of the commit?",
            "sha": "What is the hash of the commit?",
            "url": "What is the link to the commit?"
        },
        per_page='many')
    
    # Now follow the URL to get more details
    items2 = items.extract(
        {
            "username": "Who committed this commit?",
            "summary": "Summarize the extended description briefly."
        },
        per_page='one')
    
    for result in items2.limit(5):

        # Check original fields were carried through
        assert hasattr(result, 'title')
        assert hasattr(result, 'sha')
        assert hasattr(result, 'url')

        # Check new fields were added
        assert hasattr(result, 'username')
        assert hasattr(result, 'summary')

        # Username should not be empty
        assert len(result.username.strip()) > 0, "Username should not be empty"

        # URL should match expected pattern
        assert result.url.startswith("https://github.com/torvalds/linux/commit/"), \
            f"URL doesn't match expected pattern: {result.url}"

def test_04_unique_filter_workflow(fox, capsys):
    """Test unique and filter operations (quickstart3.py, quickstart4.py)."""
    # Extract commit URLs
    items = fox.extract(
        "https://github.com/torvalds/linux/commits/master/",
        {
            "url": "What is the link to the commit?"
        },
        per_page='many',
        limit=5)
    
    # Get contributor profiles
    contributor_urls = items.extract(
        {
            "username": "Who committed this commit?",
            "url": "Link to the committing user's profile. Should look like github.com/USERNAME"
        },
        per_page='one')
    
    # Apply unique filter
    unique_contributors = contributor_urls.unique('url')
    
    # Check if we can filter these contributors
    filtered_contributors = \
        unique_contributors.filter(
            "Please include all items unless they say 'test please ignore'")
    # We're just checking _that_ the filter step works, not how
    
    # Just test that the workflow runs without errors
    # Get all results to verify workflow executes fully
    results = list(filtered_contributors)
    
    # We can't guarantee filter results, but we can verify the workflow runs
    assert results is not None
    with capsys.disabled():
        print("\n### Real Activity: Two level crawl ###")
        for result in results:
            print(f"Found : {result}")
        print("### End Real Activity ###\n")


def test_05_export_functionality(fox, temp_dir):
    """Test exporting to files (from quickstart4.py)."""
    # Create a simple workflow 
    items = fox.extract(
        "https://github.com/torvalds/linux/commits/master/",
        {
            "title": "What is the title of the commit?",
            "sha": "What is the hash of the commit?",
        },
        per_page='many',
        limit=3)
    
    # Export to JSONL and CSV
    jsonl_file = os.path.join(temp_dir, "commits.jsonl")
    csv_file = os.path.join(temp_dir, "commits.csv")
    
    items.export(jsonl_file, overwrite=True)
    items.export(csv_file, overwrite=True)
    
    # Check that the files were created
    assert os.path.exists(jsonl_file), "JSONL file should exist"
    assert os.path.exists(csv_file), "CSV file should exist"
    
    # Check JSONL content
    with open(jsonl_file, 'r') as f:
        jsonl_data = [json.loads(line) for line in f]
    
    assert len(jsonl_data) > 0, "JSONL file should contain data"
    assert 'title' in jsonl_data[0], "JSONL should contain 'title' field"
    assert 'sha' in jsonl_data[0], "JSONL should contain 'sha' field"
    
    # Basic check for CSV
    with open(csv_file, 'r') as f:
        csv_content = f.read()
    
    assert len(csv_content) > 0, "CSV file should not be empty"
    assert 'title' in csv_content, "CSV should contain 'title' field"
    assert 'sha' in csv_content, "CSV should contain 'sha' field"

def test_06_multi_step_workflows(fox):
    """Test multi-step workflows (like 3_simple_workflows.py)."""
    # Get trending repos
    repos = fox.extract(
        "https://github.com/trending",
        {
            "url": "Find the URLs to the trending repositories. They should start with 'https://github.com/'"
        },
        limit=2)

    # Follow the URLs to get repo details
    repo_details = repos.extract(
        {
            "name": "What is the full name of this repository (username/repo)?",
            "description": "What is the description of this repository?",
            "stars": "How many stars does this repository have?"
        },
        per_page='one')
    
    # Get results
    results = list(repo_details)
    
    # Basic assertions
    assert len(results) > 0, "Should have at least one result"
    assert len(results) <= 2, "Should have at most 2 results due to limit"
    
    for result in results:
        assert hasattr(result, 'name')
        assert hasattr(result, 'description')
        assert hasattr(result, 'stars')
        
        # Name should contain a slash (username/repo)
        assert '/' in result.name

def test_07_concurrency(fox):
    """Test concurrency features (from 6_concurrency.py)."""
    # Create workflows for different sites
    workflow1 = fox.extract(
        "https://news.ycombinator.com",
        {"title": "Find me all the titles of the posts."},
        limit=3)
    
    workflow2 = fox.extract(
        "https://github.com/trending",
        {"title": "Find me all the names of the trending repositories."},
        limit=3)
    
    # Run concurrently with futures
    future1 = workflow1.results_future()
    future2 = workflow2.results_future()
    
    # Get results
    results1 = future1.result()
    results2 = future2.result()
    
    # Check that we got results from both sources
    assert len(results1) > 0, "Should have results from workflow1"
    assert len(results2) > 0, "Should have results from workflow2"
    
    # Check that results are accessible via the workflows too
    assert results1[0]['title'] == workflow1[0].title, "Results from future and workflow should match"

def test_extract__init_with_multiple_urls(fox):
    # List of repositories to track
    repo_list = [
        "https://github.com/torvalds/linux",
        "https://github.com/microsoft/vscode",
        "https://github.com/facebook/react"
    ]

    # Initialize workflow with multiple URLs directly
    repos_stats = fox.extract(
        repo_list,
        {
            "name": "What is the full name of this repository?",
            "stars": "How many stars does this repository have?",
            "open_issues": "How many open issues does this repository have?",
            "last_update": "When was this repository last updated?"
        },
        per_page='one'
    )

    results = list(repos_stats)

    # Should have results for each repo
    assert len(results) == len(repo_list)

    for result in results:
        assert hasattr(result, 'name')
        assert hasattr(result, 'stars')
        assert hasattr(result, 'open_issues')
        assert hasattr(result, 'last_update')

def test_detached_workflow(fox):

    some_workflow = \
        fox.extract(
            "https://fetchfox.ai",
            {"blog_post_url": "find me a url linking to the latest blog post"},
            limit=1)
    job_id = fox.run_detached(some_workflow)
    assert fox.get_results_from_detached(job_id, wait=False) is None
    results = fox.get_results_from_detached(job_id)

    assert len(results) == 1
    assert hasattr(results[0], "blog_post_url")

def test_find_urls(fox):
    urls = \
        fox.find_urls(
            "https://news.ycombinator.com",
            "Find all comments links."
        ).limit(3)

    assert len(urls) == 3
    for result in urls:
        assert "ycombinator.com/item?id=" in result._url

def test_action_step__just_that_it_doesnt_break(fox):

    summary = \
        fox.init(
            "https://news.ycombinator.com",
        ).action(
            "Click on the upvote votearrow on the first article"
            "and tell me what the page looks like after."
        ).extract(
            {"summary": "Tell me about the content on the page using fewer than 10 words."}
        ).limit(1)

    list(summary)
    assert "summary" in summary[0]




