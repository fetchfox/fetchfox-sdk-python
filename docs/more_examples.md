# More Examples

## Starting an Extraction with Multiple URLs

```python
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
        "stars": "How many stars does this repository have?"
    },
    per_page='one'
)

results = list(repos_stats)
```

## Lazy and Composable Workflows

```python
{%
	include-markdown '../examples/5_workflows_are_lazy_and_composable.py'
	comments=false
%}

```

## Concurrency

### Simple Concurrency with Futures
Using `Workflow.results_future()` will give you a standard Python [concurrent.futures.Future](https://docs.python.org/3/library/concurrent.futures.html#future-objects).

The simplest way to run multiple workflows concurrently is simply by requesting the futures and then using the results.
```python
{%
	include-markdown '../examples/6_concurrency.py'
	comments=false
	start="# <<<QS_INCLUDE_START1>>>"
    end="# <<<QS_INCLUDE_END1>>>"
%}
```