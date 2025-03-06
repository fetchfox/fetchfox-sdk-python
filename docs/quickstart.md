# Getting Started

## Installation / Setup

`pip install fetchfox-sdk`

You will need Python 3.8 or later.

### Getting an API Key

You will need an API Key to use the Fetchfox SDK.  If you want something that
runs locally, check out our [open-source core project](https://github.com/fetchfox/fetchfox).

If you are logged in to FetchFox, you can get your API key here:
[https://fetchfox.ai/settings/api-keys](https://fetchfox.ai/settings/api-keys)

## Extracting Information From Pages

Fetchfox can extract structured information from websites.  The most basic usage
is to simply give it a URL and a template that describes the structure of the items
you want to extract.

```python
{%
	include-markdown '../examples/1_extract.py'
	comments=false
%}

```
The above will provide several items that look like this:
```json
{
    "title": "Elevated errors on requests",
    "investigation_start_time": "2025-03-04 21:09 PST",
    "resolution_time": "2025-03-05 11:46 PST",
    "_url": "https://status.anthropic.com/"
}
```

## Extracting URLs

URLs are just another thing that you can extract from a page.  Simply include a
`url` field in your item template and describe how to find the URLs.

```
{%
	include-markdown '../examples/2_find_urls.py'
	comments=false
%}

```

The above will extract items like this:
```json
{ "url": "https://www.ebay.com/itm/234785237284" }
```
When you produce items with a `url` field, Fetchfox can load the those URLs in
the next step of a workflow.

## Workflows

With FetchFox, you can chain operations together.  This creates workflows.
Execution of workflows is managed on our backend.  This means you never have to worry about getting blocked, and you don't have to think about concurrency.

```python
{%
	include-markdown '../examples/3_simple_workflows.py'
	comments=false
%}

```

The above will print output similar to this:
```
Courage & Cowardice by Gene Weingarten:
    In this article, Gene Weingarten reflects on the decline of courage in journalism and the importance of having a clear moral authority. He discusses the impact of Katharine Graham's leadership and the responsibility of media organizations to uphold their values especially during critical times. Weingarten critiques the Washington Post's decision-making under pressure, emphasizing the need for integrity and honesty in reporting.
```

### Filter, Unique, and Export

FetchFox can also filter items given natural language instructions, as well as export JSONL and CSV files.
Below is an example of a longer workflow, which includes a "filter" step that will remove
some items from the previous step.

```python
{%
	include-markdown '../examples/4_workflow_filter_and_export.py'
	comments=false
%}

```
The above will produce a csv file like this:
```
MSRP,_url,frame_size,full_description,price,url
1099,https://www.bicyclebluebook.com/marketplace/buy-now,58 cm,"2020 Cannondale CAAD Optimo 3, 58 cm (XL), equipped with Shimano Sora 2x9 gears, very light use, excellent condition, always stored indoors.",950,https://www.bicyclebluebook.com/marketplace/buy-now/#1
```

Also provided is a `unique` step, which can be used to filter out any duplicate items.

```
{%
	include-markdown '../examples/5_workflows_are_lazy_and_composable.py'
	comments=false
%}

```

```
{%
	include-markdown '../examples/6_concurrency.py'
	comments=false
%}

```