import requests
import time
from typing import Dict, List, Optional, Union
import json
from urllib.parse import urljoin
import os

_API_PREFIX = "/api/v2/"

class FetchFoxSDK:
    def __init__(self, api_key: Optional[str] = None, host: str = "https://fetchfox.ai"):
        """Initialize the FetchFox SDK.
        
        Args:
            api_key: Your FetchFox API key
            host: API host URL (defaults to production)
        """
        self.base_url = urljoin(host, _API_PREFIX)

        self.api_key = api_key
        if self.api_key is None:
            self.api_key = os.environ.get("FETCHFOX_API_KEY")

        if not self.api_key:
            raise ValueError(
                "API key must be provided either as argument or "
                "in FETCHFOX_API_KEY environment variable")

        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer: {self.api_key}'
        }

    def _request(self, method: str, path: str, json_data: Optional[dict] = None) -> dict:
        """Make an API request."""
        url = urljoin(self.base_url, path)
        response = requests.request(method, url, headers=self.headers, json=json_data)
        response.raise_for_status()
        return response.json()

    def register_workflow(self, workflow: dict) -> str:
        """Create a new workflow.
        
        Args:
            workflow: Workflow configuration dictionary
            
        Returns:
            Workflow ID
        """
        response = self._request('POST', 'workflows', workflow)

        # If the response ever has other info that matters, we can add an
        # optional kwarg to get the full response and
        # continue to return just the id by default
        return response['id']

    def get_workflows(self) -> list:
        """Get workflows

        Returns:
            List of workflows
        """
        response = self._request("GET", "workflows")
        return response['results']

    def run_workflow(self, workflow_id: Optional[str] = None, workflow: Optional[dict] = None,
                    params: Optional[dict] = None) -> str:
        """Run a workflow. Either provide the ID of a registered workflow,
        or provide a workflow configuration dictionary (which will be registered
        automatically, for convenience)

        Args:
            workflow_id: ID of an existing workflow to run
            workflow: A workflow configuration dictionary to register and run
            params: Optional parameters for the workflow

        Returns:
            Job ID

        Raises:
            ValueError: If neither workflow_id nor workflow is provided
        """
        if workflow_id is None and workflow is None:
            raise ValueError(
                "Either workflow_id or workflow must be provided")

        if workflow is not None and workflow is not None:
            raise ValueError(
                "Provide only a workflow or a workflow_id, not both.")

        if params is not None:
            raise NotImplementedError("Cannot pass params to workflows yet")

        if workflow is not None:
            # Register the workflow first
            workflow_resp = self._request('POST', 'workflows', workflow)
            workflow_id = workflow_resp['id']
            print(f"Registered new workflow with id: {workflow_id}")

        response = self._request('POST', f'workflows/{workflow_id}/run', params or {})
        return response['jobId']

    def get_job_status(self, job_id: str) -> dict:
        """Get the status and results of a job.
        
        Args:
            job_id: ID of the job to check
            
        Returns:
            Job status and results
        """
        return self._request('GET', f'jobs/{job_id}')

    def await_job_completion(self, job_id: str, poll_interval: float = 5.0,
            full_response: bool = False) -> dict:
        """Wait for a job to complete and return the resulting items or full
        response.
        
        Args:
            job_id: ID of the job to wait for
            poll_interval: Time in seconds between status checks
            full_response: defaults to False, returning only the items.
            
        Returns:
            Job result items, or, if full_response, everything.
        """
        while True:
            status = self.get_job_status(job_id)
            if status.get('done'):
                if full_response:
                    return status

                else:
                    try:
                        full_items = status['results']['items']
                        import pdb
                        pdb.set_trace()
                    except KeyError:
                        print("No results.")
                        return None

                    stripped_items = [
                        {
                            k: v
                            for k, v in item.items()
                            if not k.startswith('_')
                        }
                        for item in full_items
                    ]

                    return stripped_items

            time.sleep(poll_interval)


    def _make_single_page_extraction_workflow_with_prompt():
        raise NotImplementedError()

    def _make_single_page_extraction_workflow_with_template(url, template):
        implied_workflow = {
            "steps": [
                {
                    "name": "const",
                    "args": {
                        "items": [{"url": url}],
                        "maxPages": 1
                    }
                },
                {
                    "name": "extract",
                    "args": {
                        "questions": item_template,
                        "single": True,
                        "maxPages": 1
                    }
                }
            ],
            "options": {}
        }
        return implied_workflow


    # Convenience methods that match your requirements doc
    def extract(self, url: str, instruction: Optional[str] = None,
                item_template: Optional[Dict[str, str]] = None) -> List[Dict]:
        """Extract information from a webpage using AI.

        Args:
            url: URL to extract from
            instruction: Natural language instruction for extraction
            item_template: Template with field names and questions

        Returns:
            List of extracted items
        """

        # Create a single-step workflow for single-page extraction
        if item_template and instruction:
            raise ValueError("Please provide either an item_template or"
                "a prompt, but not both.")
        if item_template is None and instruction is None:
            raise ValueError("Please provide an item_template or prompt.")

        if item_template:
            implied_workflow = \
                _make_single_page_extraction_workflow_with_template(
                    url,
                    item_template)

        elif instruction:
            implied_workflow = \
                _make_single_page_extraction_workflow_with_prompt(
                    url,
                    instruction)

        job_id = self.run_workflow(implied_workflow)
        result_items = self.await_job(job_id)
        return result_items

    def find_urls(self, url: str, instruction: str) -> List[Dict[str, str]]:
        """Find URLs on a webpage using AI.
        
        Args:
            url: Starting URL
            instruction: Natural language instruction for finding links
            
        Returns:
            List of found URLs
        """
        workflow = {
            "steps": [
                {
                    "name": "const",
                    "args": {
                        "items": [{"url": url}],
                        "maxPages": 1
                    }
                },
                {
                    "name": "crawl",
                    "args": {
                        "query": instruction,
                        "maxPages": 1
                    }
                }
            ],
            "options": {}
        }
        
        workflow_id = self.create_workflow(workflow)
        job_id = self.run_workflow(workflow_id)
        results = self.await_job(job_id)
        return results.get('items', [])