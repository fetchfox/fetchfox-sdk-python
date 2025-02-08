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
                "maxPages": 1
            }
        })
        return self

    def extract(self, template: dict) -> "Workflow":
        self._workflow["steps"].append({
            "name": "extract",
            "args": {
                "questions": template,
                "single": True,
                "maxPages": 1
            }
        })
        return self

    def limit(self, n: int) -> "Workflow":
        self._options["limit"] = n
        return self

    def to_dict(self) -> Dict[str, Any]:
        """Convert workflow to dictionary format."""
        self._workflow["options"] = self._options
        return self._workflow