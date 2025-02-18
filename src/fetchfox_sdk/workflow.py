import os
import json
import csv
from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger('fetchfox')

class Workflow:
    def __init__(self, sdk_context):

        self._sdk = sdk_context

        self._workflow = {
            "steps": [],
            "options": {}
        }

        self._results = None
        self._ran_job_id = None

    @property
    def results(self):
        """Get the results, executing the query if necessary.
        """
        if self._results is not None:
            return self._results
        else:
            self.run()
            return self._results

    def __iter__(self):
        """Make the workflow iterable.
        Accessing the results property will execute the workflow if necessary.
        """
        return iter(self.results)

    def __getitem__(self, key):
        """Allow indexing into the workflow results.
        Accessing the results property will execute the workflow if necessary.

        Args:
            key: Can be an integer index or a slice
        """
        return self.results[key]

    def __bool__(self):
        """Return True if the workflow has any results, False otherwise.
        Accessing the results property will execute the workflow if necessary.
        """
        return bool(self.results)

    def __len__(self):
        """Return the number of results.
        Accessing the results property will execute the workflow if necessary.
        """
        return len(self.results)

    def __contains__(self, item):
        """Check if an item exists in the results.
        Accessing the results property will execute the workflow if necessary.
        """
        return item in self.results

    def run(self) -> List[Dict]:
        """Execute the workflow and return results."""
        logger.debug("Running workflow.")
        job_id = self._sdk.run_workflow(workflow=self)
        results = self._sdk.await_job_completion(job_id)
        if results is None or len(results) == 0:
            print("This workflow did not return any results.")
        self._ran_job_id = job_id
        self._results = results

    def init(self, url: str) -> "Workflow":

        #TODO: Do we need to allow other data here, params?
        #TODO: if used more than once, raise error and print helpful message

        self._workflow["steps"].append({
            "name": "const",
            "args": {
                "items": [{"url": url}],
                "maxPages": 1 #TODO
            }
        })
        return self

    def configure_params(self, params) -> "Workflow":
        raise NotImplementedError()

    def export(self, filename: str, force_overwrite: bool = False) -> None:
        """Execute workflow and save results to file.

        Args:
            filename: Path to output file, must end with .csv or .jsonl
            force_overwrite: Defaults to False, which causes an error to be raised if the file exists already.  Set it to true if you want to overwrite.

        Raises:
            ValueError: If filename doesn't end with .csv or .jsonl
            FileExistsError: If file exists and force_overwrite is False
        """

        if not (filename.endswith('.csv') or filename.endswith('.jsonl')):
            raise ValueError("Output filename must end with .csv or .jsonl")

        if os.path.exists(filename) and not force_overwrite:
            raise FileExistsError(
                f"File {filename} already exists. Use force_overwrite=True to overwrite.")

        if not self.results: #accessing this property will cache the results
            if not self._ran_job_id:
                raise RuntimeError(
                    "No results and no job_id - "
                    "there may have been an uncaught problem running the job.")
            else:
                raise RuntimeError("Workflow produced no results")

        if filename.endswith('.csv'):
            fieldnames = set()
            for item in self.results:
                fieldnames.update(item.keys())

            with open(filename, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=sorted(fieldnames))
                writer.writeheader()
                writer.writerows(self.results)

        else:
            with open(filename, 'w') as f:
                for item in self.results:
                    f.write(json.dumps(item) + '\n')


    def extract(self, item_template: dict, single=None,
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
            single: set this to True if each URL has only a single item.
                    Set this to False if each URL should yield multiple items
            max_pages: enable pagination from the given URL.  Defaults to one page only.
            limit: limit the number of items yielded by this step
        """

        #TODO: call it "multiple" and default to false?  semantically clearer?
        #TODO: view: selecthtml / textonly

        if single is None:
            single = True
            self._sdk.nqprint(
                "Extracting only a single item per page in this workflow.  "
                "Pass `single=False` to extract multiple result items per page")

        self._workflow["steps"].append({
            "name": "extract",
            "args": {
                "questions": item_template,
                "single": single,
                "maxPages": max_pages,
                "limit": limit
            }
        })
        return self

    def find_urls(self, instruction: str, max_pages=1, limit=None) -> "Workflow":
        """Provide instructions which describe how to find the URLs
        you want to extract from the page.

        Example: "Find me all of the links to the detail pages for individual
        earthquakes."

        Args:
            instruction: the instruction described above
            max_pages: enable pagination from the given URL.  Defaults to one page only.
            limit: limit the number of items yielded by this step
        """
        self._workflow["steps"].append({
            "name": "crawl",
            "args": {
                "query": instruction,
                "maxPages": max_pages,
                "limit": limit
            }
        })
        return self

    def limit(self, n: int) -> "Workflow":
        if self._workflow['options'].get('limit') is not None:
            raise ValueError(
                "This limit is per-workflow, and may only be set once.")

        self._workflow['options']["limit"] = n
        return self

    #TODO: `transform()` as the underlying operation for extract AND findUrls
    #TODO: crawl

    def unique(self, fields_list: List[str], limit=None) -> "Workflow":
        """Provide a list of fields which will be used to check the uniqueness
        of the items passing through this step.

        Any items which are duplicates (as determined by these fields only),
        will be filtered and will not be seen by the next step in your workflow.

        Args:
            fields_list: the instruction described above
            limit: limit the number of items yielded by this step
        """

        self._workflow['steps'].append({
            "name": "unique",
            "args": {
                "fields": fields_list,
                "limit": limit
            }
        })

        return self

    def filter(self, instruction: str, limit=None) -> "Workflow":
        """Provide instructions for how to filter items.

        Example: "Exclude any earthquakes that were unlikely to cause significant property damage."

        Args:
            instruction: the instruction described above
            limit: limit the number of items yielded by this step
        """

        self._workflow['steps'].append({
            "name": "filter",
            "args": {
                "query": instruction,
                "limit": limit
            }
        })

        return self

    def to_dict(self) -> Dict[str, Any]:
        """Convert workflow to dictionary format."""
        return self._workflow

    def to_json(self):
        return json.dumps(self)