import requests
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Any
import json
from urllib.parse import urljoin, urlencode
import os
from .workflow import Workflow

#DBG:
from pprint import pprint

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

    def _request(self, method: str, path: str, json_data: Optional[dict] = None,
                    params: Optional[dict] = None) -> dict:
        """Make an API request.

        Args:
            method: HTTP method
            path: API path
            json_data: Optional JSON body
            params: Optional query string parameters
        """
        url = urljoin(self.base_url, path)
        response = requests.request(
            method,
            url,
            headers=self.headers,
            json=json_data,
            params=params
        )
        response.raise_for_status()
        return response.json()

    def register_workflow(self, workflow: Workflow) -> str:
        """Create a new workflow.

        Args:
            workflow: Workflow object

        Returns:
            Workflow ID
        """
        response = self._request('POST', 'workflows', workflow.to_dict())

        # NOTE: If we need to return anything else here, we should keep this
        # default behavior, but add an optional kwarg so "full_response=True"
        # can be supplied, and then we return everything
        return response['id']

    def get_workflows(self) -> list:
        """Get workflows

        Returns:
            List of workflows
        """
        response = self._request("GET", "workflows")

        # NOTE: Should we return Workflow objects intead?
        return response['results']

    def run_workflow(self, workflow_id: Optional[str] = None,
                    workflow: Optional[Workflow] = None,
                    params: Optional[dict] = None) -> str:
        """Run a workflow. Either provide the ID of a registered workflow,
        or provide a workflow object (which will be registered
        automatically, for convenience).

        You can browse https://fetcfox.ai to find publicly available workflows
        authored by others.  Copy the workflow ID and use it here.  Often,
        in this case, you will also want to provide parameters.

        Args:
            workflow_id: ID of an existing workflow to run
            workflow: A Workflow object to register and run
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
            # TODO:
            #   It sounds like these might be passed in the const/init step?
            #   Or, maybe they need to go in as a dictionary on the side?

        if workflow_id is None:
            workflow_id = self.register_workflow(workflow) # type: ignore
            print(f"Registered new workflow with id: {workflow_id}")

        #response = self._request('POST', f'workflows/{workflow_id}/run', params or {})
        response = self._request('POST', f'workflows/{workflow_id}/run')

        # NOTE: If we need to return anything else here, we should keep this
        # default behavior, but add an optional kwarg so "full_response=True"
        # can be supplied, and then we return everything
        return response['jobId']

    def get_job_status(self, job_id: str) -> dict:
        """Get the status and results of a job.  Returns partial results before
        eventually returning the full results.

        When job_status['done'] == True, the full results are present.

        NOTE: Jobs are not created immediately after you call run_workflow().
        The status will not be available until the job is scheduled, so this
        will 404 initially.
        """
        return self._request('GET', f'jobs/{job_id}')

    def await_job_completion(self, job_id: str, poll_interval: float = 5.0,
            full_response: bool = False):
        """Wait for a job to complete and return the resulting items or full
        response.

        Use "get_job_status()" if you want to manage polling yourself.
        """

        MAX_WAIT_FOR_JOB_ALIVE_MINUTES = 5
        started_waiting_for_job_dt = None

        while True:

            try:
                status = self.get_job_status(job_id)
                pprint(status)

            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 404:
                    print("Waiting for job to be scheduled.")

                    if started_waiting_for_job_dt is None:
                        started_waiting_for_job_dt = datetime.now()
                    else:
                        waited = datetime.now() - started_waiting_for_job_dt
                        if waited > timedelta(minutes=MAX_WAIT_FOR_JOB_ALIVE_MINUTES):
                            raise RuntimeError(
                                f"Job {job_id} is taking unusually long to schedule.")

                    status = {}
                else:
                    raise

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

    def _plan_extraction_from_url_and_prompt(self,
            url: str, instruction: str) -> Workflow:

        fetch_response = self._request('GET', 'fetch', params={'url': url})
        html_url = fetch_response['html']

        plan_response = self._request('POST', 'plan/from-prompt', {
            "prompt": instruction,
            "urls": [url],
            "html": html_url
        })

        return Workflow.from_dict(plan_response)


    def extract(self, url: str, instruction: Optional[str] = None,
                item_template: Optional[Dict[str, str]] = None) -> List[Dict]:
        """Extract information from a webpage using AI."""
        if item_template and instruction:
            raise ValueError(
                "Please provide either an item_template or a prompt, but not both.")
        if item_template is None and instruction is None:
            raise ValueError("Please provide an item_template or prompt.")

        implied_workflow = Workflow().init(url)

        if item_template:
            implied_workflow.extract(item_template)
        else:
            implied_workflow = \
                self._plan_extraction_from_url_and_prompt(
                    url,
                    instruction)

        job_id = self.run_workflow(workflow=implied_workflow)
        # The workflow will be registered and run, but in this convenience
        # function, the user doesn't care about that.

        return self.await_job_completion(job_id)

    def find_urls(self, url: str, instruction: str, max_pages: int = 1) -> List[Dict[str, str]]:
        """Find URLs on a webpage using AI."""
        implied_workflow = (
            Workflow()
            .init(url)
            .find_urls(instruction, max_pages=max_pages)
        )

        job_id = self.run_workflow(workflow=implied_workflow)
        return self.await_job_completion(job_id)