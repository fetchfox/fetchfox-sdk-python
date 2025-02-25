import requests
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Any
import json
from pprint import pformat
from urllib.parse import urljoin, urlencode
import os
import sys
import logging
from .workflow import Workflow

logger = logging.getLogger('fetchfox')

_API_PREFIX = "/api/v2/"

class FetchFoxSDK:
    def __init__(self,
            api_key: Optional[str] = None, host: str = "https://fetchfox.ai",
            quiet=False):
        """Initialize the FetchFox SDK.

        You may also provide an API key in the environment variable `FETCHFOX_API_KEY`.

        Args:
            api_key: Your FetchFox API key.  Overrides the environment variable.
            host: API host URL (defaults to production)
            quiet: set to True to suppress printing
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

        self.quiet = False

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
            params=params,
            timeout=(30,30)
        )

        response.raise_for_status()
        body = response.json()

        logger.debug(
            f"Response from %s %s:\n%s  at %s",
            method, path, pformat(body), datetime.now())
        return body

    def _nqprint(self, *args, **kwargs):
        if not self.quiet:
            print(*args, **kwargs)

    def workflow(self, url: str = None, params:dict = None) -> "Workflow":
        """Create a new workflow using this SDK instance.

        Examples of how to use a workflow:

        ```
        city_pages = fox \
            .workflow("https://locations.traderjoes.com/pa/") \
            .extract(
                item_template = {
                    "url": "Find me all the URLs for the city directories"
                }
            )
        ```

        A workflow is kind of like a Django QuerySet.  It will not be executed
        until you attempt to use the results.

        ```
        list_of_city_pages = list(city_pages)
        # This would run the workflow and give you a list of items like:
            {'url': 'https://....'}
        ```

        You could export those results to a file:
        ```
        city_pages.export("city_urls.jsonl")
        city_pages.export("city_urls.csv")
        ```

        And then you could create a new workflow (or two) that use those results:

        ```
        store_info = city_pages.extract(
            item_template = {
                "store_address": "find me the address of the store",
                "store_number": "Find me the number of the store (it's in parentheses)",
                "store_phone": "Find me the phone number of the store"
                }
        )

        store_urls = city_pages.extract(
            item_template = {
                "url": "Find me the URLs of Store detail pages."
            }
        )
        ```

        In the above snippets, the `city_pages` workflow was only ever executed
        once.

        Optionally, a URL and/or params may be passed here to initialize
        the workflow with them.

        Workflow parameters are given in a dictionary.  E.g. if your workflow
        has a `{{state_name}}` parameter, you might pass:

            { 'state_name': 'Alaska' }

        or perhaps

            { 'state_name': ['Alaska', 'Hawaii'] }

        if you wish to run the workflow for both states and collect the results.

        Args:
            url: URL to start from
            params: Workflow parameters.
        """
        w = Workflow(self)
        if url:
            w = w.init(url)
        if params:
            w = w.configure_params(params)

        return w

    def workflow_from_json(self, json_workflow) -> "Workflow":
        """Given a JSON string, such as you can generate in the wizard at
        https://fetchfox.ai, create a workflow from it.

        Once created, it can be used like a regular workflow.

        Args:
            json_workflow: This must be a valid JSON string that represents a Fetchfox Workflow.  You should not usually try to write these manually, but simply copy-paste from the web interface.
        """
        return self.workflow_from_dict(json.loads(json_workflow))

    def _workflow_from_dict(self, workflow_dict):
        w = Workflow(self)
        w._workflow = workflow_dict
        return w


    def workflow_by_id(self, workflow_id) -> "Workflow":
        """Use a public workflow ID

        Something like fox.workflow_by_id(ID).configure_params({state:"AK"}).export("blah.csv")

        """
        workflow_json = self.get_workflow(workflow_id)
        return self.workflow_from_json(workflow_json)

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

    def get_workflow(self, id) -> dict:
        """Get a registered workflow by ID."""
        response = self._request("GET", f"workflow/{id}")
        return response

    def _run_workflow(self, workflow_id: Optional[str] = None,
                    workflow: Optional[Workflow] = None,
                    params: Optional[dict] = None) -> str:
        """Run a workflow. Either provide the ID of a registered workflow,
        or provide a workflow object (which will be registered
        automatically, for convenience).

        You can browse https://fetchfox.ai to find publicly available workflows
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

        if workflow is not None and not isinstance(workflow, Workflow):
            raise ValueError(
                "The workflow argument must be a fetchfox_sdk.Workflow")
        if workflow_id and not isinstance(workflow_id, str):
            raise ValueError(
                "The workflow_id argument must be a string "
                "representing a registered workflow's ID")

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
        self._nqprint(f"Waiting for job [{job_id}] to finish: ")

        while True:

            try:
                status = self.get_job_status(job_id)
                self._nqprint(".", end="")
                sys.stdout.flush()
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
                self._nqprint("\n")

                if full_response:
                    return status

                # Otherwise, process the status into result items that match
                # the item_template (optionally retaining _url for find_urls())
                try:
                    full_items = status['results']['items']
                except KeyError:
                    nqprint("No results.")
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

        return self._workflow_from_dict(plan_response)
