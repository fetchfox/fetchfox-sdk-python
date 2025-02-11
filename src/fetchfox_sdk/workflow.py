import json
from typing import Optional, Dict, Any

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
        self._workflow["steps"].append({
            "name": "const",
            "args": {
                "items": [{"url": url}],
                "maxPages": 1 #TODO
            }
        })
        return self

    def extract(self, template: dict) -> "Workflow":
        self._workflow["steps"].append({
            "name": "extract",
            "args": {
                "questions": template,
                "single": True, #TODO
                "maxPages": 1 #TODO - This will paginate too!
                #todo: limit
                #TODO:
                #   view: selecthtml / textonly
            }
        })
        return self

    ##TODO: transform (is extract AND findUrls)

    def limit(self, n: int) -> "Workflow":
        if self._workflow['options'].get('limit') is not None:
            raise ValueError(
                "This limit is per-workflow, and may only be set once.")

        self._workflow['options']["limit"] = n
        return self

    def find_urls(self, instruction: str, max_pages=1) -> "Workflow":
        self._workflow["steps"].append({
            "name": "crawl",
            "args": {
                "query": instruction,
                "maxPages": max_pages #TODO: None means no pagination, >=1 means paginate
                #TODO: generated code in app also shows a limit:null here?
                #TODO: limit items can be here
            }
        })
        return self

    #TODO:
    #crawl


    def unique(self, field: str) -> "Workflow":
        raise NotImplementedError
        #return self

    def to_dict(self) -> Dict[str, Any]:
        """Convert workflow to dictionary format."""
        return self._workflow

    def to_json(self):
        return json.dumps(self)