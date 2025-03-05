<a id="src/fetchfox_sdk"></a>

# src/fetchfox\_sdk

<a id="src/fetchfox_sdk.client"></a>

# src/fetchfox\_sdk.client

<a id="src/fetchfox_sdk.client.FetchFoxSDK"></a>

## FetchFoxSDK Objects

```python
class FetchFoxSDK()
```

<a id="src/fetchfox_sdk.client.FetchFoxSDK.__init__"></a>

#### \_\_init\_\_

```python
def __init__(api_key: Optional[str] = None,
             host: str = "https://fetchfox.ai",
             quiet=False)
```

Initialize the FetchFox SDK.

You may also provide an API key in the environment variable `FETCHFOX_API_KEY`.

**Arguments**:

- `api_key` - Your FetchFox API key.  Overrides the environment variable.
- `host` - API host URL (defaults to production)
- `quiet` - set to True to suppress printing

<a id="src/fetchfox_sdk.client.FetchFoxSDK.workflow"></a>

#### workflow

```python
def workflow(url: str = None, params: dict = None) -> "Workflow"
```

Create a new workflow using this SDK instance.

Examples of how to use a workflow:


A workflow is kind of like a Django QuerySet.  It will not be executed
until you attempt to use the results.


You could export those results to a file:

And then you could create a new workflow (or two) that use those results:


In the above snippets, the `city_pages` workflow was only ever executed
once.

Optionally, a URL and/or params may be passed here to initialize
the workflow with them.

Workflow parameters are given in a dictionary.  E.g. if your workflow
has a `{{state_name}}` parameter, you might pass:

{ 'state_name': 'Alaska' }

or perhaps

{ 'state_name': ['Alaska', 'Hawaii'] }

if you wish to run the workflow for both states and collect the results.

```
city_pages = fox             .workflow("https://locations.traderjoes.com/pa/")             .extract(
        item_template = {
            "url": "Find me all the URLs for the city directories"
        }
    )
```
```
list_of_city_pages = list(city_pages)
# This would run the workflow and give you a list of items like:
    {'url': 'https://....'}
```
```
city_pages.export("city_urls.jsonl")
city_pages.export("city_urls.csv")
```
```
store_info = city_pages.extract(
    item_template = {
        "store_address": "find me the address of the store",
        "store_number": "Find me the number of the store (it's in parentheses)",
        "store_phone": "Find me the phone number of the store"
        }
)

store_urls = city_pages.extract(
    item_template = {
        "url": "Find me the URLs of Store detail pages."
    }
)
```

**Arguments**:

- `url` - URL to start from
- `params` - Workflow parameters.

<a id="src/fetchfox_sdk.client.FetchFoxSDK.workflow_from_json"></a>

#### workflow\_from\_json

```python
def workflow_from_json(json_workflow) -> "Workflow"
```

Given a JSON string, such as you can generate in the wizard at
https://fetchfox.ai, create a workflow from it.

Once created, it can be used like a regular workflow.

**Arguments**:

- `json_workflow` - This must be a valid JSON string that represents a Fetchfox Workflow.  You should not usually try to write these manually, but simply copy-paste from the web interface.

<a id="src/fetchfox_sdk.client.FetchFoxSDK.workflow_by_id"></a>

#### workflow\_by\_id

```python
def workflow_by_id(workflow_id) -> "Workflow"
```

Use a public workflow ID

Something like fox.workflow_by_id(ID).configure_params({state:"AK"}).export("blah.csv")

<a id="src/fetchfox_sdk.client.FetchFoxSDK.register_workflow"></a>

#### register\_workflow

```python
def register_workflow(workflow: Workflow) -> str
```

Create a new workflow.

**Arguments**:

- `workflow` - Workflow object
  

**Returns**:

  Workflow ID

<a id="src/fetchfox_sdk.client.FetchFoxSDK.get_workflows"></a>

#### get\_workflows

```python
def get_workflows() -> list
```

Get workflows

**Returns**:

  List of workflows

<a id="src/fetchfox_sdk.client.FetchFoxSDK.get_workflow"></a>

#### get\_workflow

```python
def get_workflow(id) -> dict
```

Get a registered workflow by ID.

<a id="src/fetchfox_sdk.client.FetchFoxSDK.get_job_status"></a>

#### get\_job\_status

```python
def get_job_status(job_id: str) -> dict
```

Get the status and results of a job.  Returns partial results before
eventually returning the full results.

When job_status['done'] == True, the full results are present in
response['results']['items'].

If you want to manage your own polling, you can use this instead of
await_job_completion()

NOTE: Jobs are not created immediately after you call run_workflow().
The status will not be available until the job is scheduled, so this
will 404 initially.

<a id="src/fetchfox_sdk.client.FetchFoxSDK.await_job_completion"></a>

#### await\_job\_completion

```python
def await_job_completion(job_id: str,
                         poll_interval: float = 5.0,
                         full_response: bool = False,
                         keep_urls: bool = False)
```

Wait for a job to complete and return the resulting items or full
response.

Use "get_job_status()" if you want to manage polling yourself.

**Arguments**:

- `job_id` - the id of the job, as returned by run_workflow()
- `poll_interval` - in seconds
- `full_response` - defaults to False, so we return the result_items only.  Pass full_response=True if you want to access the entire body of the final response.
- `keep_urls` - defaults to False so result items match the given item template.  Set to true to include the "_url" property.  Not necessary if _url is the ONLY key.

<a id="src/fetchfox_sdk.client.FetchFoxSDK.just_extract"></a>

#### just\_extract

```python
def just_extract(url: str,
                 instruction: Optional[str] = None,
                 item_template: Optional[Dict[str, str]] = None,
                 mode=None,
                 max_pages=1,
                 limit=None) -> List[Dict]
```

Extract items from a given URL, given either a prompt or a template.

An instructional prompt is just natural language instruction describing
the desired results.

The options "mode", "max_pages", and "limit" may NOT be given with
"instruction". These options may only be provided with an item template.

Use an item_template when you want to specify output fieldnames.

An item template is a dictionary where the keys are the desired
output fieldnames and the values are the instructions for extraction of
that field.

Example item templates:
{
"magnitude": "What is the magnitude of this earthquake?",
"location": "What is the location of this earthquake?",
"time": "What is the time of this earthquake?"
}

{
"url": "Find me all the links to the product detail pages."
}

To follow pagination, provide max_pages > 1.

**Arguments**:

- `instruction` - an instructional prompt as described above
- `item_template` - the item template described above
- `mode` - 'single'|'multiple'|'auto' - defaults to 'auto'.  Set this to 'single' if each URL has only a single item.  Set this to 'multiple' if each URL should yield multiple items
- `max_pages` - enable pagination from the given URL.  Defaults to one page only.
- `limit` - limit the number of items yielded by this step

<a id="src/fetchfox_sdk.workflow"></a>

# src/fetchfox\_sdk.workflow

<a id="src/fetchfox_sdk.workflow.Workflow"></a>

## Workflow Objects

```python
class Workflow()
```

<a id="src/fetchfox_sdk.workflow.Workflow.results"></a>

#### results

```python
@property
def results()
```

Get the results, executing the query if necessary.

<a id="src/fetchfox_sdk.workflow.Workflow.has_results"></a>

#### has\_results

```python
@property
def has_results()
```

If you want to check whether a workflow has results already, but
do NOT want to trigger execution yet.

<a id="src/fetchfox_sdk.workflow.Workflow.__iter__"></a>

#### \_\_iter\_\_

```python
def __iter__()
```

Make the workflow iterable.
Accessing the results property will execute the workflow if necessary.

<a id="src/fetchfox_sdk.workflow.Workflow.__getitem__"></a>

#### \_\_getitem\_\_

```python
def __getitem__(key)
```

Allow indexing into the workflow results.
Accessing the results property will execute the workflow if necessary.
NOTE: Workflows will NEVER execute partially.  Accessing any item of
the results will always trigger a complete execution.

**Arguments**:

- `key` - Can be an integer index or a slice

<a id="src/fetchfox_sdk.workflow.Workflow.__bool__"></a>

#### \_\_bool\_\_

```python
def __bool__()
```

Return True if the workflow has any results, False otherwise.
Accessing the results property will execute the workflow if necessary.

<a id="src/fetchfox_sdk.workflow.Workflow.__len__"></a>

#### \_\_len\_\_

```python
def __len__()
```

Return the number of results.
Accessing the results property will execute the workflow if necessary.

<a id="src/fetchfox_sdk.workflow.Workflow.__contains__"></a>

#### \_\_contains\_\_

```python
def __contains__(item)
```

Check if an item exists in the results.
Accessing the results property will execute the workflow if necessary.

<a id="src/fetchfox_sdk.workflow.Workflow.run"></a>

#### run

```python
def run() -> List[Dict]
```

Execute the workflow and return results.

Note that running the workflow will attach the results to it.  After it
has results, derived workflows will be given the _results_ from this workflow,
NOT the steps of this workflow.

<a id="src/fetchfox_sdk.workflow.Workflow.export"></a>

#### export

```python
def export(filename: str, force_overwrite: bool = False) -> None
```

Execute workflow and save results to file.

**Arguments**:

- `filename` - Path to output file, must end with .csv or .jsonl
- `force_overwrite` - Defaults to False, which causes an error to be raised if the file exists already.  Set it to true if you want to overwrite.
  

**Raises**:

- `ValueError` - If filename doesn't end with .csv or .jsonl
- `FileExistsError` - If file exists and force_overwrite is False

<a id="src/fetchfox_sdk.workflow.Workflow.extract"></a>

#### extract

```python
def extract(item_template: dict,
            mode=None,
            view=None,
            limit=None,
            max_pages=1) -> "Workflow"
```

Provide an item_template which describes what you want to extract
from the URLs processed by this step.

The keys of this template are the fieldnames,
and the values are the instructions for extracting that field.

**Examples**:

  {
- `"magnitude"` - "What is the magnitude of this earthquake?",
- `"location"` - "What is the location of this earthquake?",
- `"time"` - "What is the time of this earthquake?"
  }
  
  {
- `"url"` - "Find me the URLs of the product detail pages."
  }
  

**Arguments**:

- `item_template` - the item template described above
- `mode` - 'single'|'multiple'|'auto' - defaults to 'auto'.  Set this to 'single' if each URL has only a single item.  Set this to 'multiple' if each URL should yield multiple items
- `max_pages` - enable pagination from the given URL.  Defaults to one page only.
- `limit` - limit the number of items yielded by this step
- `view` - TODO - you may select a subset of the page content for processing

<a id="src/fetchfox_sdk.workflow.Workflow.limit"></a>

#### limit

```python
def limit(n: int) -> "Workflow"
```

Limit the total number of results that this workflow will produce.

<a id="src/fetchfox_sdk.workflow.Workflow.unique"></a>

#### unique

```python
def unique(fields_list: List[str], limit=None) -> "Workflow"
```

Provide a list of fields which will be used to check the uniqueness
of the items passing through this step.

Any items which are duplicates (as determined by these fields only),
will be filtered and will not be seen by the next step in your workflow.

**Arguments**:

- `fields_list` - the instruction described above
- `limit` - limit the number of items yielded by this step

<a id="src/fetchfox_sdk.workflow.Workflow.filter"></a>

#### filter

```python
def filter(instruction: str, limit=None) -> "Workflow"
```

Provide instructions for how to filter items.

Example: "Exclude any earthquakes that were unlikely to cause significant property damage."

**Arguments**:

- `instruction` - the instruction described above
- `limit` - limit the number of items yielded by this step

<a id="src/fetchfox_sdk.workflow.Workflow.to_dict"></a>

#### to\_dict

```python
def to_dict() -> Dict[str, Any]
```

Convert workflow to dictionary format.

