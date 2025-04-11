# Key Concepts

FetchFox is a powerful scraping tool.  It uses AI to scrape webpages intelligently.

## Workflows

Every operation is a workflow.  You can chain operations together into longer workflows.  These operations are called 'steps'.  Each step is given the previous step's output as its input.

### Workflow Steps

#### Extract
This is the most fundamental step.  It loads a webpage and extracts the requested information.

Usually, your workflows should start with an `extract()` step, provided with a starting URL.

The `extract()` step always takes URLs as input.  When it's used later in a workflow, it will operate on the URLs provided by the _previous_ step.

So, if your step generates items with a `url` field, and you follow that step with an `extract()` step, that will load each of those URLs and extract the requested data from each of those pages.

This step has a `limit` option which is different from the global limit step.  It allows you to limit the numbef of items _this_ step will generate.

#### Extract Operates on Multiple URLs

When passed multiple items from previous steps, the `extract()` step will process them all.  When you're using `extract()` as your first step, you can also provide it with multiple URLs.  Just pass a list of URLs instead of a single URL.

#### Filter
You can't use the `filter()` step as the _first_ step in your workflow, since it does not generate any items.  When you use it after a step that yields items, it will have access to those items.

To use `filter()`, you provide natural language instructions to the AI.  Each item will be processed according to these instructions and will be excluded or included in the output accordingly.

#### Unique
The unique step, like `filter()`, cannot be used as the first step.  It takes a list of fieldnames with respect to the items it accepts as input.  The input items will be deduplicated, with only the given fields being considered.

You can also pass a single fieldname without wrapping it in a list.

For example, suppose your previous step generated items like this:
```
{"name": "Alice", "id": "123"}
{"name": "Bob", "id": "456"}
{"name": "Charlie", "id": "456"}
{"name": "Dennis", "id": "789"}
{"name": "Alice", "id": "000"}
```

If you filtered by `name`, one of the "Alice" items would be removed.

If you filtered by `id`, one of the items with id `456` would be removed.

If you filtered by `['name','id']`, then **no** items would be removed, because they are all unique when considered this way.

#### Limit
The limit step may only be used once in a workflow, and sets a global limit on the number of items that will be generated as output.  This does **not** place any limits on the intermediate steps.

### Workflows Are Lazy and Composable

Workflows will not be executed until their results are needed.  You can also create branching workflows by creating multiple that inherit from a single parent workflow.

### Workflows Carry Results

After executed, a workflow will carry it's results cached, so that using these results multiple times won't run the workflow multiple times.

When you chain onto a workflow that already has results, the child workflows will be initialized with the existing results.  This is great, because you can create a workflow, look at the results, and then extend it without re-executing the part that already ran.

## Execution

Workflows are executed on the FetchFox backend.  We handle request concurrency and proxying.

### Concurrent Workflow Execution

You can also run multiple entire workflows concurrently.  See [the example here](../more_examples/#simple-concurrency-with-futures)

### Detached Workflow Execution

You can run a workflow "detached", which just means that it will persist (and continue running on the server) even if your client is interrupted.

For example:
```
some_workflow = fox.extract(some_url, {"some_feature": "some instruction"})
job_id = fox.run_detached(some_workflow)
```
Now, that process can exit or be killed, but if you've kept the `job_id`, you can get the results later:
```
results = fox.get_results_from_detached(job_id)
```

By default, the above will block until the results are complete.  If you simply want to check
whether or not the results are ready, you can use `fox.get_results_from_detached(wait=False)`.