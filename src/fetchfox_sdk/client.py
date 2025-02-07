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

        self.api_key = api_key or os.environ.get("FETCHFOX_API_KEY")
        if not self.api_key:
            raise ValueError(
                "API key must be provided either as argument or "
                "in FETCHFOX_API_KEY environment variable")

        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer: {api_key}'
        }

    def _request(self, method: str, path: str, json_data: Optional[dict] = None) -> dict:
        """Make an API request."""
        url = urljoin(self.base_url, path)
        response = requests.request(method, url, headers=self.headers, json=json_data)
        response.raise_for_status()
        return response.json()

    def register_workflow(self, workflow) -> str:
        """Create a new workflow.
        
        Args:
            workflow: Workflow configuration object, may be either a JSON string
                      or a dict serializable to JSON
            
        Returns:
            Workflow ID
        """
        response = self._request('POST', '/workflows', workflow)
        return response

    def run_workflow(self, workflow_id: str, params: Optional[dict] = None) -> str:
        """Run a workflow.
        
        Args:
            workflow_id: ID of the workflow to run
            params: Optional parameters for the workflow
            
        Returns:
            Job ID
        """
        response = self._request('POST', f'/workflows/{workflow_id}/run', params or {})
        return response['jobId']

    def get_job_status(self, job_id: str) -> dict:
        """Get the status and results of a job.
        
        Args:
            job_id: ID of the job to check
            
        Returns:
            Job status and results
        """
        return self._request('GET', f'/jobs/{job_id}')

    def await_job(self, job_id: str, poll_interval: float = 5.0) -> dict:
        """Wait for a job to complete and return its results.
        
        Args:
            job_id: ID of the job to wait for
            poll_interval: Time in seconds between status checks
            
        Returns:
            Job results
        """
        while True:
            status = self.get_job_status(job_id)
            if status.get('done'):
                return status.get('results', {})
            time.sleep(poll_interval)

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
        # Create a single-step workflow for extraction
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
                    "name": "extract",
                    "args": {
                        "questions": item_template if item_template else {"result": instruction},
                        "single": True,
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

    def crawl(self, url: str, instruction: str) -> List[Dict[str, str]]:
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