import requests
import time
from typing import Dict, List, Optional, Union
import json
from urllib.parse import urljoin
import os
from .workflow import Workflow

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

    def register_workflow(self, workflow: Union[Workflow, dict]) -> str:
        """Create a new workflow.

        Args:
            workflow: Workflow object or configuration dictionary

        Returns:
            Workflow ID
        """
        if isinstance(workflow, Workflow):
            workflow_dict = workflow.to_dict()
        else:
            workflow_dict = workflow

        response = self._request('POST', 'workflows', workflow_dict)
        return response['id']

    def get_workflows(self) -> list:
        """Get workflows

        Returns:
            List of workflows
        """
        response = self._request("GET", "workflows")
        return response['results']

    def run_workflow(self, workflow_id: Optional[str] = None,
                    workflow: Optional[Union[Workflow, dict]] = None,
                    params: Optional[dict] = None) -> str:
        """Run a workflow. Either provide the ID of a registered workflow,
        or provide a workflow configuration (which will be registered
        automatically, for convenience)

        Args:
            workflow_id: ID of an existing workflow to run
            workflow: A Workflow object or configuration dictionary to register and run
            params: Optional parameters for the workflow

        Returns:
            Job ID

        Raises:
            ValueError: If neither workflow_id nor workflow is provided
        """
        if workflow_id is None and workflow is None:
            raise ValueError(
                "Either workflow_id or workflow must be provided")

        if workflow_id is not None and workflow is not None:
            raise ValueError(
                "Provide only a workflow or a workflow_id, not both.")

        if params is not None:
            raise NotImplementedError("Cannot pass params to workflows yet")

        if workflow is not None:
            # Convert Workflow object to dict if needed
            if isinstance(workflow, Workflow):
                workflow_dict = workflow.to_dict()
            else:
                workflow_dict = workflow

            # Register the workflow first
            workflow_id = self.register_workflow(workflow_dict)
            print(f"Registered new workflow with id: {workflow_id}")

        response = self._request('POST', f'workflows/{workflow_id}/run', params or {})
        return response['jobId']

    def get_job_status(self, job_id: str) -> dict:
        """Get the status and results of a job."""
        return self._request('GET', f'jobs/{job_id}')

    def await_job_completion(self, job_id: str, poll_interval: float = 5.0,
            full_response: bool = False) -> dict:
        """Wait for a job to complete and return the resulting items or full
        response."""
        while True:
            status = self.get_job_status(job_id)
            if status.get('done'):
                if full_response:
                    return status

                try:
                    full_items = status['results']['items']
                except KeyError:
                    print("No results.")
                    return None

                stripped_items = [
                    {k: v for k, v in item.items() if not k.startswith('_')}
                    for item in full_items
                ]

                return stripped_items

            time.sleep(poll_interval)

    def extract(self, url: str, instruction: Optional[str] = None,
                item_template: Optional[Dict[str, str]] = None) -> List[Dict]:
        """Extract information from a webpage using AI."""
        if item_template and instruction:
            raise ValueError(
                "Please provide either an item_template or a prompt, but not both.")
        if item_template is None and instruction is None:
            raise ValueError("Please provide an item_template or prompt.")

        workflow = Workflow().init(url)

        if item_template:
            workflow.extract(item_template)
        else:
            # This will raise NotImplementedError as per the current implementation
            raise NotImplementedError("Extraction with instruction not yet implemented")

        job_id = self.run_workflow(workflow=workflow)
        return self.await_job_completion(job_id)

    def find_urls(self, url: str, instruction: str, max_pages: int = 1) -> List[Dict[str, str]]:
        """Find URLs on a webpage using AI."""
        workflow = (
            Workflow()
            .init(url)
            .find_urls(instruction, max_pages=max_pages)
        )

        job_id = self.run_workflow(workflow=workflow)
        return self.await_job_completion(job_id)