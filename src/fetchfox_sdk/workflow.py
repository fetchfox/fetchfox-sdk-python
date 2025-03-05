import os
import copy
import json
import csv
from typing import Optional, Dict, Any, List, Generator, Union
import logging
import concurrent.futures
import threading

from .result_item import ResultItem

logger = logging.getLogger('fetchfox')

class Workflow:

    _executor = concurrent.futures.ThreadPoolExecutor()

    def __init__(self, sdk_context):

        self._sdk = sdk_context

        self._workflow = {
            "steps": [],
            "options": {}
        }

        self._results = None
        self._ran_job_id = None
        self._future = None
        self._callback_thread = None
        self._stop_callback = threading.Event()
        self._lock = threading.Lock()

    @property
    def all_results(self):
        """Get all results, executing the query if necessary, blocks until done.
        Returns results as ResultItem objects for easier attribute access.
        """
        if not self.has_results:
            self._run__block_until_done() # writes to self._results

        return [ResultItem(item) for item in self._results]

    def results(self):
        yield from self._results_gen()

    @property
    def has_results(self):
        """If you want to check whether a workflow has results already, but
        do NOT want to trigger execution yet."""
        if self._results is None:
            return False
        return True

    @property
    def has_run(self):
        """If this workflow has been executed before (even if there were no
        results)
        """
        if self._ran_job_id is not None:
            return True
        return False

    def __iter__(self) -> Generator[ResultItem, None, None]:
        """Make the workflow iterable.
        Accessing the results property will execute the workflow if necessary.
        """
        # Use the results property which already returns ResultItems
        yield from self.results()

    def __getitem__(self, key):
        """Allow indexing into the workflow results.
        Accessing the results property will execute the workflow if necessary.
        NOTE: Workflows will NEVER execute partially.  Accessing any item of
        the results will always trigger a complete execution.

        Args:
            key: Can be an integer index or a slice
        """
        # Results property already returns ResultItems
        return self.all_results[key]

    def __bool__(self):
        """Return True if the workflow has any results, False otherwise.
        Accessing the results property will execute the workflow if necessary.
        """
        return bool(self.all_results)

    def __len__(self):
        """Return the number of results.
        Accessing the results property will execute the workflow if necessary.
        """
        return len(self.all_results)

    def __contains__(self, item):
        """Check if an item exists in the results.
        Accessing the results property will execute the workflow if necessary.
        """
        return item in self.all_results

    def _clone(self):
        """Create a new instance with copied workflow OR copied results"""
        # check underlying, not property, because we don't want to trigger exec
        if self._results is None or len(self._results) < 1:
            # If there are no results, we are extending the steps of this workflow
            # so that, when it runs, we'll produce the desired results
            if self._ran_job_id is not None:
                #TODO - anything else we should do when we've run but no results?
                logger.debug("Cloning a job that ran, but which had no results")

            new_instance = Workflow(self._sdk)
            new_instance._workflow = copy.deepcopy(self._workflow)
            return new_instance
        else:
            # We purportedly have more than zero results:
            # We are disposing of the steps that have been executed.
            # The results are now used for workflows that derive from this one,
            # This allows re-using a workflow to make many deriviatives without
            # re-executing it or having to manually initialize them from
            # the results
            new_instance = Workflow(self._sdk)
            new_instance._workflow["steps"] = [
                {
                    "name": "const",
                    "args": {
                        "items": copy.deepcopy(self._results)
                        # We use the internal _results field, because it's a
                        # list of dictionaries rather than ResultItems
                    }
                }
            ]
            return new_instance

    #TODO: refresh?
    #Force a re-run, even though results are present?

    def _run__block_until_done(self) -> List[Dict]:
        """Execute the workflow and return results.

        Note that running the workflow will attach the results to it.  After it
        has results, derived workflows will be given the _results_ from this workflow,
        NOT the steps of this workflow.
        """
        logger.debug("Running workflow to completion")
        return list(self._results_gen())

    def _results_gen(self):
        """Generator yields results as they are available from the job.
        Attaches results to workflow as it proceeds, so they are later available
        without running again.
        """

        logger.debug("Streaming Results")
        if not self.has_results:
            self._results = []
            job_id = self._sdk._run_workflow(workflow=self)
            self._ran_job_id = job_id #track that we have ran
            for item in self._sdk._job_result_items_gen(job_id):
                self._results.append(item)
                yield ResultItem(item)
        else:
            yield from self.all_results #yields ResultItems

    def _future_done_cb(self, future):
        """Done-callback: triggered when the future completes
        (success, fail, or cancelled).
        We store final results if everything’s okay;
        otherwise, we can handle exceptions.
        """
        if not future.cancelled():
            self._results = future.result()
        else:
            self._future = None

    def results_future(self):
        """Returns a plain concurrent.futures.Future object that yields ALL results
        when the job is complete.  Access the_future.result() to block, or use
        the_future.done() to check for completion without any blocking.

        If we already have results, they will be immediately available in the
        `future.result()`
        """

        with self._lock:
            if self._callback_thread is not None:
                raise RuntimeError(
                    "Cannot call results_future() if you have a running"
                    "callback thread already.")

            if self._results is not None:
                # Already have final results: return a completed future
                completed_future = concurrent.futures.Future()
                completed_future.set_result(self._results)
                self._future = completed_future

            if self._future is not None:
                # Already started, so reuse existing future
                return self._future

            self._future = self._executor.submit(self._run__block_until_done)
            self._future.add_done_callback(self._future_done_cb)
            return self._future

    def run_with_callback_for_result_items(self, on_item, on_exc=None):
        """Run this workflow in the background.  Provide a callback function
        and this function will be called each time a new result item arrives.

        Args:
            on_item: Function that accepts a single result item as input.  Will be run
                upon each new result item as they arrive.
        """
        with self._lock:
            # Don’t allow callback mode if we have a running or completed future
            if self._future is not None:
                raise RuntimeError(
                    "Cannot use item callback mode while a future"
                    " is in flight.")
            if self._callback_thread is not None:
                raise RuntimeError(
                    "Refusing to start a duplicate callback thread.")

            # Reset event in case it’s set from a previous usage
            self._stop_callback.clear()
            self._callback_thread = threading.Thread(
                target=self._callback_runner,
                args=(on_item,on_exc),
                daemon=False
            )
            self._callback_thread.start()

    def _callback_runner(self, on_item, on_exc):
        """Just runs _results_gen in the background and calls the callback
        for each new item"""
        collected = []
        try:
            for result_item in self._results_gen():
                if self._stop_callback.is_set():
                    break
                collected.append(dict(result_item))
                on_item(result_item)
            with self._lock:
                self._results = collected
        except Exception as e:
            on_exc(e)
        finally:
            with self._lock:
                self._callback_thread = None

    def wait_until_done(self):
        """
        Blocks until the item callback thread has completed (if it is running).
        Ensures the main thread can wait so it doesn't exit prematurely.
        """
        # get the callback thread safely
        with self._lock:
            thread = self._callback_thread

        if thread is not None:
            thread.join()

    def init(self, url: Union[str, List[str]]) -> "Workflow":
        """Initialize the workflow with one or more URLs.

        Args:
            url: Can be a single URL as a string, or a list of URLs.
        """
        #TODO: if used more than once, raise error and print helpful message
        #TODO: do params here?

        new_instance = self._clone()

        if isinstance(url, str):
            items = [{"url": url}]
        else:
            items = [{"url": u} for u in url]

        new_instance._workflow["steps"].append({
            "name": "const",
            "args": {
                "items": items,
                "maxPages": 1 #TODO
            }
        })
        return new_instance

    def configure_params(self, params) -> "Workflow":
        raise NotImplementedError()

    def export(self, filename: str, overwrite: bool = False) -> None:
        """Execute workflow and save results to file.

        Args:
            filename: Path to output file, must end with .csv or .jsonl
            overwrite: Defaults to False, which causes an error to be raised if the file exists already.  Set it to true if you want to overwrite.

        Raises:
            ValueError: If filename doesn't end with .csv or .jsonl
            FileExistsError: If file exists and overwrite is False
        """

        if not (filename.endswith('.csv') or filename.endswith('.jsonl')):
            raise ValueError("Output filename must end with .csv or .jsonl")

        if os.path.exists(filename) and not overwrite:
            raise FileExistsError(
                f"File {filename} already exists. Use overwrite=True to overwrite.")

        if self.has_run:
            if not self.has_results:
                raise RuntimeError("A job ran, but there are no results.")

            # If it has run, and results is not None, results could still be []
            # anyway, accessing it here won't trigger another run
            if len(self.all_results) < 1:
                if os.path.exists(filename) and overwrite:
                    raise RuntimeError("No results.  Refusing to overwrite.")
                else:
                    self._sdk._nqprint("No results to export.")

        # Now we access the magic property, so execution will occur if needed
        raw_results = [ dict(result_item) for result_item in self.all_results ]

        if filename.endswith('.csv'):
            fieldnames = set()
            for item in raw_results:
                fieldnames.update(item.keys())

            with open(filename, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=sorted(fieldnames))
                writer.writeheader()
                writer.writerows(raw_results)

        else:
            with open(filename, 'w') as f:
                for item in raw_results:
                    f.write(json.dumps(item) + '\n')


    def extract(self, item_template: dict, mode=None, view=None,
            limit=None, max_pages=1) -> "Workflow":
        """Provide an item_template which describes what you want to extract
        from the URLs processed by this step.

        The keys of this template are the fieldnames,
        and the values are the instructions for extracting that field.

        Examples:
        {
            "magnitude": "What is the magnitude of this earthquake?",
            "location": "What is the location of this earthquake?",
            "time": "What is the time of this earthquake?"
        }

        {
            "url": "Find me the URLs of the product detail pages."
        }

        Args:
            item_template: the item template described above
            mode: 'single'|'multiple'|'auto' - defaults to 'auto'.  Set this to 'single' if each URL has only a single item.  Set this to 'multiple' if each URL should yield multiple items
            max_pages: enable pagination from the given URL.  Defaults to one page only.
            limit: limit the number of items yielded by this step
            view: 'html' | 'selectHtml' | 'text' - defaults to HTML (the full HTML).  Use 'selectHTML' to have the AI see only text and links.  Use 'text' to have the AI see only text.
        """
        # Validate field names to prevent collisions with ResultItem methods
        RESERVED_PROPERTIES = {'keys', 'items', 'values', 'to_dict', 'get'}

        for field_name in item_template.keys():
            if field_name in RESERVED_PROPERTIES:
                raise ValueError(
                    f"Field name '{field_name}' is a reserved property name. "
                    f"Please choose a different field name. "
                    f"Reserved names are: {', '.join(RESERVED_PROPERTIES)}"
                )

        if mode is not None and mode not in ["single", "multiple", "auto"]:
            raise ValueError("Mode may only be 'single'|'multiple'|'auto'")

        new_instance = self._clone()

        new_step = {
            "name": "extract",
            "args": {
                "questions": item_template,
                "maxPages": max_pages,
                "limit": limit,
            }
        }

        if view is not None:
            new_step['args']['view'] = view

        if mode is not None:
            new_step['args']['mode'] = mode

        new_instance._workflow["steps"].append(new_step)

        return new_instance

    def limit(self, n: int) -> "Workflow":
        """
        Limit the total number of results that this workflow will produce.
        """
        if self._workflow['options'].get('limit') is not None:
            raise ValueError(
                "This limit is per-workflow, and may only be set once.")

        #TODO: if there are results, I think we could actually carry them through?
        new_instance = self._clone()
        new_instance._workflow['options']["limit"] = n
        return new_instance

    def unique(self, fields_list: List[str], limit=None) -> "Workflow":
        """Provide a list of fields which will be used to check the uniqueness
        of the items passing through this step.

        Any items which are duplicates (as determined by these fields only),
        will be filtered and will not be seen by the next step in your workflow.

        Args:
            fields_list: the instruction described above
            limit: limit the number of items yielded by this step
        """
        new_instance = self._clone()

        new_instance._workflow['steps'].append({
            "name": "unique",
            "args": {
                "fields": fields_list,
                "limit": limit
            }
        })

        return new_instance

    def filter(self, instruction: str, limit=None) -> "Workflow":
        """Provide instructions for how to filter items.

        Example: "Exclude any earthquakes that were unlikely to cause significant property damage."

        Args:
            instruction: the instruction described above
            limit: limit the number of items yielded by this step
        """
        new_instance = self._clone()
        new_instance._workflow['steps'].append({
            "name": "filter",
            "args": {
                "query": instruction,
                "limit": limit
            }
        })

        return new_instance

    def to_dict(self) -> Dict[str, Any]:
        """Convert workflow to dictionary format."""
        return self._workflow

    def to_json(self):
        return json.dumps(self._workflow)
