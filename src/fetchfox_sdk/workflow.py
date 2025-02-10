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

    def __init__(self):
        self._workflow = {"steps": []}
        self._options = {}

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
                "maxPages": 1 #TODO
            }
        })
        return self

    def limit(self, n: int) -> "Workflow":
        self._workflow.options["limit"] = n
        #TODO: This is a global limit, and if used multiple times, will silently
        #overwrite the last setting.  Raise error if limit is already set,
        # to call attention to intended use and actual function?
        return self

    def find_urls(self, instruction: str, max_pages=1) -> "Workflow":
	    self._workflow["steps"].append({
	        "name": "crawl",
	        "args": {
	            "query": instruction,
	            "maxPages": max_pages #TODO
	            #TODO: generated code in app also shows a limit:null here?
	        }
	    })
	    return self

	def unique(self, field: str) -> "Workflow":
	    raise NotImplementedError
	    #return self

	def to_dict(self) -> Dict[str, Any]:
        """Convert workflow to dictionary format."""
        self._workflow["options"] = self._options
        return self._workflow

	def __json__(self):
		return self.to_dict()

	def to_json(self):
		return json.dumps(self)