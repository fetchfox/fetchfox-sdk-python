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
def __init__(api_key: Optional[str] = None, host: str = "https://fetchfox.ai")
```

Initialize the FetchFox SDK.

**Arguments**:

- `api_key` - Your FetchFox API key
- `host` - API host URL (defaults to production)

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

<a id="src/fetchfox_sdk.client.FetchFoxSDK.run_workflow"></a>

#### run\_workflow

```python
def run_workflow(workflow_id: Optional[str] = None,
                 workflow: Optional[Workflow] = None,
                 params: Optional[dict] = None) -> str
```

Run a workflow. Either provide the ID of a registered workflow,
or provide a workflow object (which will be registered
automatically, for convenience).

You can browse https://fetchfox.ai to find publicly available workflows
authored by others.  Copy the workflow ID and use it here.  Often,
in this case, you will also want to provide parameters.

**Arguments**:

- `workflow_id` - ID of an existing workflow to run
- `workflow` - A Workflow object to register and run
- `params` - Optional parameters for the workflow
  

**Returns**:

  Job ID
  

**Raises**:

- `ValueError` - If neither workflow_id nor workflow is provided

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

<a id="src/fetchfox_sdk.client.FetchFoxSDK.extract"></a>

#### extract

```python
def extract(url: str,
            instruction: Optional[str] = None,
            item_template: Optional[Dict[str, str]] = None,
            single=False,
            max_pages=1,
            limit=None) -> List[Dict]
```

Extract items from a given URL, given either a prompt or a template.

An instructional prompt is just natural language instruction describing
the desired results.

The options "single", "max_pages", and "limit" may NOT be given with
"instruction". These options may only be provided with an item template.

An item template is a dictionary where the keys are the desired
output fieldnames and the values are the instructions for extraction of
that field.

Example item template:
{
"magnitude": "What is the magnitude of this earthquake?",
"location": "What is the location of this earthquake?",
"time": "What is the time of this earthquake?"
}

To follow pagination, provide max_pages > 1.

**Arguments**:

- `instruction` - an instructional prompt as described above
- `item_template` - the item template described above
- `single` - Defaults to False. Set this to True if each URL has only a single item to extract.
- `max_pages` - enable pagination from the given URL.  Defaults to one page only.
- `limit` - limit the number of items yielded by this step

<a id="src/fetchfox_sdk.client.FetchFoxSDK.find_urls"></a>

#### find\_urls

```python
def find_urls(url: str,
              instruction: str,
              max_pages: int = 1,
              limit=None) -> List[str]
```

Find URLs on a webpage using AI, given an instructional prompt.

An instructional prompt is just natural language instruction describing
the desired results.

Example Instructional Prompts:
"Find me all the links to bicycles that are not electric 'e-bikes'"
"Find me the links to each product detail page."
"Find me the links for each US State"
"Find me the links to the profiles for employees among the C-Suite"

**Arguments**:

- `instruction` - an instructional prompt as described above
- `max_pages` - provide an integer > 1 if you want to follow pagination
- `limit` - limits the number of items yielded by this step

<a id="src/fetchfox_sdk.workflow"></a>

# src/fetchfox\_sdk.workflow

<a id="src/fetchfox_sdk.workflow.Workflow"></a>

## Workflow Objects

```python
class Workflow()
```

<a id="src/fetchfox_sdk.workflow.Workflow.from_json"></a>

#### from\_json

```python
@classmethod
def from_json(cls, json_str: str) -> "Workflow"
```

Create a workflow from a JSON string.

<a id="src/fetchfox_sdk.workflow.Workflow.from_dict"></a>

#### from\_dict

```python
@classmethod
def from_dict(cls, workflow_dict: dict) -> "Workflow"
```

Create a workflow from a dictionary.

<a id="src/fetchfox_sdk.workflow.Workflow.extract"></a>

#### extract

```python
def extract(item_template: dict,
            single=None,
            limit=None,
            max_pages=1) -> "Workflow"
```

Provide an item_template which describes what you want to extract
from the URLs processed by this step.

The keys of this template are the fieldnames,
and the values are the instructions for extracting that field.

**Example**:

  {
- `"magnitude"` - "What is the magnitude of this earthquake?",
- `"location"` - "What is the location of this earthquake?",
- `"time"` - "What is the time of this earthquake?"
  }
  

**Arguments**:

- `item_template` - the item template described above
- `single` - set this to True if each URL has only a single item.
  Set this to False if each URL should yield multiple items
- `max_pages` - enable pagination from the given URL.  Defaults to one page only.
- `limit` - limit the number of items yielded by this step

<a id="src/fetchfox_sdk.workflow.Workflow.find_urls"></a>

#### find\_urls

```python
def find_urls(instruction: str, max_pages=1, limit=None) -> "Workflow"
```

Provide instructions which describe how to find the URLs
you want to extract from the page.

Example: "Find me all of the links to the detail pages for individual
earthquakes."

**Arguments**:

- `instruction` - the instruction described above
- `max_pages` - enable pagination from the given URL.  Defaults to one page only.
- `limit` - limit the number of items yielded by this step

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

