# Getting Started

## Installation / Setup

`pip install fetchfox-sdk`

You will need Python 3.8 or later.

### Getting an API Key

You will need an API Key to use the Fetchfox SDK.  If you want something that
runs locally, check out our [open-source core project](https://github.com/fetchfox/fetchfox).

If you are logged in to FetchFox, you can get your API key here:
[https://fetchfox.ai/settings/api-keys](https://fetchfox.ai/settings/api-keys)

#### Configuration
If you export the `FETCHFOX_API_KEY` environment variable, the SDK will use that.
You can also provide the key when initializing the SDK like this:
```
FetchFox(api_key="YOUR_API_KEY_HERE")
```
---
## Example: Extracting Information from GitHub

### Simple Extraction

Fetchfox can extract structured information from websites.  The most basic usage
is to simply give it a URL and a template that describes the structure of the items
you want to extract.

```python
{%
	include-markdown '../examples/quickstart/quickstart1.py'
	comments=false
%}
```
The above will output something like this:
```json
{
    "forks": "55.4k",
    "stars": "189k",
    "name": "torvalds/linux",
    "_url": "https://github.com/torvalds/linux"
}
```

### Extracting Multiple Items

FetchFox can extract multiple items from one page.

```python
{%
    include-markdown '../examples/quickstart/quickstart2.py'
    comments=false
    start="# <<<QS_INCLUDE_START>>>"
    end="# <<<QS_INCLUDE_END>>>"
%}
```

The above will extract commit titles and hashes.

#### Pagination

If you specify `max_pages`, FetchFox will use AI to load subsequent pages after
your starting URL.

```python
{%
    include-markdown '../examples/quickstart/quickstart2_paginate.py'
    comments=false
    start="# <<<QS_INCLUDE_START>>>"
    end="# <<<QS_INCLUDE_END>>>"
%}
```
This works like the previous example, but loads many more results.

#### Extraction Modes: Single and Multiple

You may have noticed the `mode` parameter being used in extractions.  This controls how many items will be yielded per page.

You can specify `single` or `multiple`.  If you don't provide this parameter, FetchFox will use AI to guess, based on your template and the contents of the page.

### Following URLs

URLs are just another thing that you can extract from a page.  Simply include a
`url` field in your item template and describe how to find the URLs.

When you produce items with a `url` field, Fetchfox can load the those URLs in
the next step of a workflow.

```python
{%
    include-markdown '../examples/quickstart/quickstart2.5.py'
    comments=false
    start="# <<<QS_INCLUDE_START>>>"
    end="# <<<QS_INCLUDE_END>>>"
%}
```
Now, we can extend that workflow by chaining another step.  This will load the pages for the
individual commits and extract information from those pages.
```python
{%
    include-markdown '../examples/quickstart/quickstart2.5.py'
    comments=false
    start="# <<<QS_INCLUDE_START2>>>"
    end="# <<<QS_INCLUDE_END2>>>"
%}
```

### Workflows

With FetchFox, you can chain operations together.  This creates workflows.
Execution of workflows is managed on our backend.

Let's extend the examples above to look at the authors of the ten most recent commits
and see how many GitHub followers they have.

To accomplish this, we'll use the following steps:

1. Load the list of commits and get a URL for each individual commit
2. Load each individual commit and get a URL for the author
3. Remove any duplicate authors (the same user may have made multiple commits)
4. Load each unique author's page and extract their follower count

```python
{%
	include-markdown '../examples/quickstart/quickstart3.py'
	comments=false
    start="# <<<QS_INCLUDE_START>>>"
    end="# <<<QS_INCLUDE_END>>>"
%}
```

The above will print output similar to this:
```
torvalds has 229k followers
[...]
```

#### Filter and Export

FetchFox can also filter items given natural language instructions.

Let's look at the list of commits and find some that are related to networking,
then export their extended descriptions to a file.

```python
{%
	include-markdown '../examples/quickstart/quickstart4.py'
	comments=false
    start="# <<<QS_INCLUDE_START>>>"
    end="# <<<QS_INCLUDE_END>>>"
%}

```
The above will produce a JSONL file with lines like this:
```
{
    "title": "Merge tag 'net-6.14-rc6' of [...]"
    "sha": "f315296c92fd4b7716bdea17f727ab431891dc3b",
    "_url": "https://github.com/torvalds/linux/commits/master/"
}
```

#### More About Workflows
Workflow are lazy, carry results with them, and may be run concurrently.  See [concepts](../concepts) and [more examples](../more_examples).