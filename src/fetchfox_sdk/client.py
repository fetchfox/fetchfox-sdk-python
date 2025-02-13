import requests
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Any
import json
from pprint import pformat
from urllib.parse import urljoin, urlencode
import os
import logging
from .workflow import Workflow

logger = logging.getLogger('fetchfox')

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
        body = response.json()

        logger.debug(f"Response from %s %s:\n%s", method, path, pformat(body))
        return body

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
            # TODO:
            #   https://docs.google.com/document/d/17ieru_HfU3jXBilcZqL1Ksf27rsVPvOIQ8uxmHi2aeE/edit?disco=AAABdjyFjgw
            #   allow list-expansion here like above, pretty cool

        if workflow_id is None:
            workflow_id = self.register_workflow(workflow) # type: ignore
            logger.info("Registered new workflow with id: %s", workflow_id)

        #response = self._request('POST', f'workflows/{workflow_id}/run', params or {})
        response = self._request('POST', f'workflows/{workflow_id}/run')

        # NOTE: If we need to return anything else here, we should keep this
        # default behavior, but add an optional kwarg so "full_response=True"
        # can be supplied, and then we return everything
        return response['jobId']

    def get_job_status(self, job_id: str) -> dict:
        """Get the status and results of a job.  Returns partial results before
        eventually returning the full results.

        When job_status['done'] == True, the full results are present in
        response['results']['items'].

        If you want to manage your own polling, you can use this instead of
        await_job_completion()

        NOTE: Jobs are not created immediately after you call run_workflow().
        The status will not be available until the job is scheduled, so this
        will 404 initially.
        """
        return self._request('GET', f'jobs/{job_id}')

    def await_job_completion(self, job_id: str, poll_interval: float = 5.0,
            full_response: bool = False, keep_urls: bool = False):
        """Wait for a job to complete and return the resulting items or full
        response.

        Use "get_job_status()" if you want to manage polling yourself.

        Args:
            job_id: the id of the job, as returned by run_workflow()
            poll_interval: in seconds
            full_response: defaults to False, so we return the result_items only.  Pass full_response=True if you want to access the entire body of the final response.
            keep_urls: defaults to False so result items match the given item template.  Set to true to include the "_url" property.  Not necessary if _url is the ONLY key.
        """

        MAX_WAIT_FOR_JOB_ALIVE_MINUTES = 5 #TODO: reasonable?
        started_waiting_for_job_dt = None

        while True:

            try:
                status = self.get_job_status(job_id)

            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 404:

                    logger.info("Waiting for job %s to be scheduled.", job_id)

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

                # Otherwise, process the status into result items that match
                # the item_template (optionally retaining _url for find_urls())
                try:
                    full_items = status['results']['items']
                except KeyError:
                    print("No results.")
                    return None

                stripped_items = []
                for item in full_items:
                    # First get just the non-underscore keys
                    filtered_item = {
                        k: v
                        for k, v
                        in item.items()
                        if not k.startswith('_')
                    }

                    # Keep _url if explicitly requested OR if we have no other keys
                    if (keep_urls or not filtered_item) and '_url' in item:
                        filtered_item['_url'] = item['_url']

                    stripped_items.append(filtered_item)

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
                item_template: Optional[Dict[str, str]] = None,
                single=False, max_pages=1, limit=None) -> List[Dict]:
        """Extract items from a given URL, given either a prompt or a template.

        An instructional prompt is just natural language instruction describing
        the desired results.

        The options "single", "max_pages", and "limit" may NOT be given with
        "instruction". These options may only be provided with an item template.

        An item template is a dictionary where the keys are the desired
        output fieldnames and the values are the instructions for extraction of
        that field.

        Example item template:
        {
            "magnitude": "What is the magnitude of this earthquake?",
            "location": "What is the location of this earthquake?",
            "time": "What is the time of this earthquake?"
        }

        To follow pagination, provide max_pages > 1.

        Args:
            instruction: an instructional prompt as described above
            item_template: the item template described above
            single: Defaults to False. Set this to True if each URL has only a single item to extract.
            max_pages: enable pagination from the given URL.  Defaults to one page only.
            limit: limit the number of items yielded by this step
        """

        if item_template and instruction:
            raise ValueError(
                "Please provide either an item_template or a prompt, but not both.")
        if item_template is None and instruction is None:
            raise ValueError("Please provide an item_template or prompt.")

        implied_workflow = Workflow().init(url)

        if item_template:
            implied_workflow.extract(
                item_template,
                single=single,
                max_pages=max_pages,
                limit=limit
            )
        else:
            # if these options are set to anything other than their defaults,
            # warn, because they are not being respected.
            # We could also throw an error here.

            if single:
                print("Warning: 'single' will be ignored in instruction mode.")
            if max_pages != 1:
                print("Warning: 'max_pages' will be ignored in instruction mode.")
            if limit is not None:
                print("Warning: 'limit' will be ignored in instruction mode.")

            implied_workflow = \
                self._plan_extraction_from_url_and_prompt(
                    url,
                    instruction)

        job_id = self.run_workflow(workflow=implied_workflow)
        # The workflow will be registered and run, but in this convenience
        # function, the user doesn't care about that.

        result_items = self.await_job_completion(job_id)
        return result_items

    def find_urls(self, url: str, instruction: str, max_pages: int = 1,
            limit=None) -> List[str]:
        """Find URLs on a webpage using AI, given an instructional prompt.

         An instructional prompt is just natural language instruction describing
        the desired results.

        Example Instructional Prompts:
            "Find me all the links to bicycles that are not electric 'e-bikes'"
            "Find me the links to each product detail page."
            "Find me the links for each US State"
            "Find me the links to the profiles for employees among the C-Suite"

        Args:
            instruction: an instructional prompt as described above
            max_pages: provide an integer > 1 if you want to follow pagination
            limit: limits the number of items yielded by this step
        """
        implied_workflow = (
            Workflow()
            .init(url)
            .find_urls(instruction, max_pages=max_pages, limit=limit)
        )

        job_id = self.run_workflow(workflow=implied_workflow)
        urls_as_items = self.await_job_completion(job_id, keep_urls=True)
        return [ item['_url'] for item in urls_as_items ]