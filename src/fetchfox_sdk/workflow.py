import json
from typing import Optional, Dict, Any, List

class Workflow:
    @classmethod
    def from_json(cls, json_str: str) -> "Workflow":
        """Create a workflow from a JSON string."""
        workflow_dict = json.loads(json_str)
        workflow = cls()
        workflow._workflow = workflow_dict
        return workflow

    @classmethod
    def from_dict(cls, workflow_dict: dict) -> "Workflow":
        """Create a workflow from a dictionary."""
        workflow = cls()
        workflow._workflow = workflow_dict
        #TODO: We could actually implement validation in __init__
        #TODO: maybe this should not be here at all, might confuse.
        return workflow

    def __init__(self):
        self._workflow = {
            "steps": [],
            "options": {}
        }

    def init(self, url: str) -> "Workflow":

        #TODO: Do we need to allow other data here?

        self._workflow["steps"].append({
            "name": "const",
            "args": {
                "items": [{"url": url}],
                "maxPages": 1 #TODO
            }
        })
        return self

    def extract(self, item_template: dict, single=None,
            limit=None, max_pages=1) -> "Workflow":
        """Provide an item_template which describes what you want to extract
        from the URLs processed by this step.

        The keys of this template are the fieldnames,
        and the values are the instructions for extracting that field.

        Example:
        {
            "magnitude": "What is the magnitude of this earthquake?",
            "location": "What is the location of this earthquake?",
            "time": "What is the time of this earthquake?"
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
            print(
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