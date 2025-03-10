# More Examples

## Lazy and Composable Workflows

```
{%
	include-markdown '../examples/5_workflows_are_lazy_and_composable.py'
	comments=false
%}

```

## Concurrency

### Simple Concurrency with Futures
Using `Workflow.results_future()` will give you a standard Python [concurrent.futures.Future](https://docs.python.org/3/library/concurrent.futures.html#future-objects).

The simplest way to run multiple workflows concurrently is simply by requesting the futures and then using the results.
```
{%
	include-markdown '../examples/6_concurrency.py'
	comments=false
	start="# <<<QS_INCLUDE_START1>>>"
    end="# <<<QS_INCLUDE_END1>>>"
%}
```