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
from concurrent.futures import ThreadPoolExecutor
from queue import Queue
import threading

from .workflow import Workflow

logger = logging.getLogger('fetchfox')

_API_PREFIX = "/api/v2/"

class FetchFox:
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

        self.quiet = quiet
        self._executor = ThreadPoolExecutor(max_workers=1)
        # TODO: this needs to be changed to support concurrent job polling,
        # but I am setting it to 1 right now as a sanity-check


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

    def _workflow(self, url_or_urls: Union[str, List[str]] = None) -> "Workflow":
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
        if url_or_urls:
            w = w.init(url_or_urls)
        # if params:
        #     w = w.configure_params(params)

        return w

    def workflow_from_json(self, json_workflow) -> "Workflow":
        """Given a JSON string, such as you can generate in the wizard at
        https://fetchfox.ai, create a workflow from it.

        Once created, it can be used like a regular workflow.

        Args:
            json_workflow: This must be a valid JSON string that represents a Fetchfox Workflow.  You should not usually try to write these manually, but simply copy-paste from the web interface.
        """
        return self._workflow_from_dict(json.loads(json_workflow))

    def _workflow_from_dict(self, workflow_dict):
        w = Workflow(self)
        w._workflow = workflow_dict
        return w

    def workflow_by_id(self, workflow_id) -> "Workflow":
        """Use a public workflow ID

        Something like fox.workflow_by_id(ID).configure_params({state:"AK"}).export("blah.csv")

        """
        workflow_json = self._get_workflow(workflow_id)
        return self.workflow_from_json(workflow_json)

    def _register_workflow(self, workflow: Workflow) -> str:
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

    def _get_workflows(self) -> list:
        """Get workflows

        Returns:
            List of workflows
        """
        response = self._request("GET", "workflows")

        # NOTE: Should we return Workflow objects intead?
        return response['results']

    def _get_workflow(self, id) -> dict:
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
            workflow_id = self._register_workflow(workflow) # type: ignore
            logger.info("Registered new workflow with id: %s", workflow_id)

        #response = self._request('POST', f'workflows/{workflow_id}/run', params or {})
        response = self._request('POST', f'workflows/{workflow_id}/run')

        # NOTE: If we need to return anything else here, we should keep this
        # default behavior, but add an optional kwarg so "full_response=True"
        # can be supplied, and then we return everything
        return response['jobId']

    def _get_job_status(self, job_id: str) -> dict:
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

    def _poll_status_once(self, job_id):
        """Poll until we get one status response.  This may be more than one poll,
        if it is the first one, since the job will 404 for a while before
        it is scheduled."""
        MAX_WAIT_FOR_JOB_ALIVE_MINUTES = 5 #TODO: reasonable?
        started_waiting_for_job_dt = None
        while True:
            try:
                status = self._get_job_status(job_id)
                self._nqprint(".", end="")
                sys.stdout.flush()

                #TODO print partial status?

                return status
            except requests.exceptions.HTTPError as e:
                if e.response.status_code in [404, 500]:
                    self._nqprint("x", end="")
                    sys.stdout.flush()
                    logger.info("Waiting for job %s to be scheduled.", job_id)

                    if started_waiting_for_job_dt is None:
                        started_waiting_for_job_dt = datetime.now()
                    else:
                        waited = datetime.now() - started_waiting_for_job_dt
                        if waited > timedelta(minutes=MAX_WAIT_FOR_JOB_ALIVE_MINUTES):
                            raise RuntimeError(
                                f"Job {job_id} is taking unusually long to schedule.")

                else:
                    raise

    def _cleanup_job_result_item(self, item):
        filtered_item = {
            k: v
            for k, v
            in item.items()
            if not k.startswith('_')
        }

        # TODO: What should we be doing with `_url`?
        # # Keep _url if we have no other keys
        # if not filtered_item and '_url' in item:
        filtered_item['_url'] = item['_url']
        return filtered_item

    def _job_result_items_gen(self, job_id):
        """Yield new result items as they arrive."""
        self._nqprint(f"Streaming results from: [{job_id}]: ")

        seen_ids = set() # We need to track which have been yielded already

        MAX_WAIT_FOR_CHANGE_MINUTES = 5
        # Job will be assumed done/stalled after this much time passes without
        # a new result coming in.
        first_response_dt = None
        results_changed_dt = None

        while True:
            response = self._poll_status_once(job_id)
            # The above will block until we get one successful response
            if not first_response_dt:
                first_response_dt = datetime.now()

            # We are considering only the result_items here, not partials
            if 'items' not in response['results']:
                waited_dur = datetime.now() - first_response_dt
                if waited_dur > timedelta(minutes=MAX_WAIT_FOR_CHANGE_MINUTES):
                    raise RuntimeError(
                        "This job is taking too long - please retry.")
                continue

            for job_result_item in response['results']['items']:
                jri_id = job_result_item['_meta']['id']
                if jri_id not in seen_ids:
                    # We have a new result_item
                    results_changed_dt = datetime.now()
                    seen_ids.add(jri_id)
                    self._nqprint("")
                    yield self._cleanup_job_result_item(job_result_item)

            if results_changed_dt:
                waited_dur2 = results_changed_dt - datetime.now()
                if waited_dur2 > timedelta(minutes=MAX_WAIT_FOR_CHANGE_MINUTES):
                    # It has been too long since we've seen a new result, so
                    # we will assume the job is stalled on the server
                    break

            if response.get("done") == True:
                break

            time.sleep(1)

    def extract(self, url_or_urls, *args, **kwargs):
        """Extract items from a given URL, given an item template.

        An item template is a dictionary where the keys are the desired
        output fieldnames and the values are the instructions for extraction of
        that field.

        Example item templates:
        {
            "magnitude": "What is the magnitude of this earthquake?",
            "location": "What is the location of this earthquake?",
            "time": "What is the time of this earthquake?"
        }

        {
            "url": "Find me all the links to the product detail pages."
        }

        To follow pagination, provide max_pages > 1.

        Args:
            item_template: the item template described above
            per_page: 'one'|'many'|'auto' - defaults to 'auto'.  Set this to 'one' if each URL has only a single item.  Set this to 'many' if each URL should yield multiple items
            max_pages: enable pagination from the given URL.  Defaults to one page only.
            limit: limit the number of items yielded by this step
        """
        return self._workflow(url_or_urls).extract(*args, **kwargs)

    def init(self, url_or_urls, *args, **kwargs):
        """Initialize the workflow with one or more URLs.

        Args:
            url: Can be a single URL as a string, or a list of URLs.
        """
        return self._workflow(url_or_urls)

    def filter(*args, **kwargs):
        raise RuntimeError("Filter cannot be the first step.")


    def unique(*args, **kwargs):
        raise RuntimeError("Unique cannot be the first step.")