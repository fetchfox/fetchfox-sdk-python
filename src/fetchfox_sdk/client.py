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
import signal

from .workflow import Workflow
from .item import Item


TRACE = 5
logging.addLevelName(TRACE, "TRACE")
def trace(self, message, *args, **kwargs):
    if self.isEnabledFor(TRACE):
        self._log(TRACE, message, args, **kwargs)
logging.Logger.trace = trace

_API_PREFIX = "/api/v2/"

class FetchFox:
    _LOG_LEVELS = {
        "trace": TRACE,
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warning": logging.WARNING,
        "error": logging.ERROR,
        "critical": logging.CRITICAL,
    }

    def __init__(self,
            api_key: Optional[str] = None, host: str = "https://fetchfox.ai",
            log_level="warning"):
        """Initialize the FetchFox SDK.

        You may also provide an API key in the environment variable `FETCHFOX_API_KEY`.

        Args:
            api_key: Your FetchFox API key.  Overrides the environment variable.
            host: API host URL (defaults to production)
            log_level: debug|info|warning|error|critical, print logs >= this level to the console
        """

        self.base_url = urljoin(host, _API_PREFIX)

        self.api_key = api_key
        if self.api_key is None:
            self.api_key = os.environ.get("FETCHFOX_API_KEY")

        if not self.api_key:
            raise ValueError(
                "API key must be provided either as an argument or "
                "in FETCHFOX_API_KEY environment variable.  Find your key at: \n"
                "https://fetchfox.ai/settings/api-keys")

        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer: {self.api_key}'
        }

        # Convert log_level argument to a logging constant
        if isinstance(log_level, str):
            log_level = self._LOG_LEVELS.get(log_level.lower(), logging.WARNING)
        self.log_level = log_level

        # Configure the logger
        self.logger = logging.getLogger("fetchfox")
        self.logger.setLevel(self.log_level)

        # Create a default handler to print to console
        if not self.logger.handlers:  # but only if no handler is present
            ch = logging.StreamHandler(sys.stdout)
            ch.setLevel(self.log_level)
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            ch.setFormatter(formatter)
            self.logger.addHandler(ch)

        self._executor = ThreadPoolExecutor(max_workers=1)
        # TODO: this needs to be changed to support concurrent job polling,
        # but I am setting it to 1 right now as a sanity-check

        self._attached_jobs = []
        try:
            signal.signal(signal.SIGINT, self._handle_signit)
        except ValueError:
            # If we're not in the main thread, we can't do this --e.g. flask req
            pass

    def _handle_signit(self, sig, frame):
        """
        On Ctrl-c, abort any attached jobs (not touching detached jobs)
        """
        for job_id in self._attached_jobs:
            try:
                self._request("POST", f"jobs/{job_id}/stop")
                self.logger.warning(f"Aborted job: {job_id}")
            except Exception as e:
                self.logger.error("Failed to abort job [{job_id}]: {e}")
        sys.exit(1)


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

        per_page='many'
        self.logger.trace(
            f"Response from %s %s:\n%s  at %s",
            method, path, pformat(body), datetime.now())
        return body

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

        Returns:
            A workflow object.
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

    def run_detached(self, workflow):
        """Run a workflow without watching for the results.  Returns a job_id
        which can be queried later by calling
        FetchFoxSDK.get_results_from_detached(job_id).
        You can exit this process, and get the results later.

        Args:
            workflow: a workflow object.
        """

        # Exposing this separately rather than exposing "_run_workflow", because
        # it would likely confuse people to have a function called "run_workflow"
        # that they should not normally use.
        return self._run_workflow(workflow=workflow, detached=True)

    def get_results_from_detached(self, job_id, wait=True):
        """Pass a job_id and retrieve the results.  By default, will *wait* for
        the job to finish and will return the complete results.

        If you want to not block, pass wait=False and either the complete results
        or `None` will be returned.

        Args:
            job_id: job_id from `FetchFoxSDK.run_detached()`
            wait: use wait=False to get an immediate response, which will either be the full results or None if the job is not yet complete.
        Returns:
            The full results of the job.  Or, if wait=False and the job is not done, None.
        """

        if wait:
            return [
                Item(result)
                for result
                in list(self._job_result_items_gen(job_id))
            ]
        else:
            resp = self._poll_status_once(job_id, detached_skip_wait=True)
            if not resp:
                return None
            if not resp.get('done'):
                return None
            else:
                results = [
                    self._cleanup_job_result_item(e)
                    for e
                    in resp['results']['items']
                ]

                return [ Item(result) for result in results ]


    def _run_workflow(self, workflow_id: Optional[str] = None,
                    workflow: Optional[Workflow] = None, detached=False,
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
            self.logger.info("Registered new workflow with id: %s", workflow_id)

        #response = self._request('POST', f'workflows/{workflow_id}/run', params or {})
        response = self._request('POST', f'workflows/{workflow_id}/run')
        if not detached:
            self._attached_jobs.append(response['jobId'])

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

    def _poll_status_once(self, job_id, detached_skip_wait=False):
        """Poll until we get one status response.  This may be more than one poll,
        if it is the first one, since the job will 404 for a while before
        it is scheduled."""
        MAX_WAIT_FOR_JOB_ALIVE_MINUTES = 5 #TODO: reasonable?
        started_waiting_for_job_dt = None
        while True:
            try:
                status = self._get_job_status(job_id)
                sys.stdout.flush()

                return status
            except requests.exceptions.HTTPError as e:
                if detached_skip_wait:
                    return None

                if e.response.status_code in [404, 500]:
                    sys.stdout.flush()
                    self.logger.info("Waiting for job %s to be scheduled.", job_id)

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
        # TODO: cleanup?
        return item

    def _job_result_items_gen(self, job_id,
            raw_log_level=logging.ERROR,
            log_summaries_dest=None,
            intermediate_items_dest=None):
        """Yield new result items as they arrive.
        Log_summaries_dest can be a list that accumulates logs"""
        self.logger.info(f"Streaming results from: [{job_id}]: ")

        seen_ids = set() # We need to track which have been yielded already
        seen_log_summaries = set()
        seen_logs = set()
        seen_intermediate_item_ids = set()

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

            try:
                if log_summaries_dest is not None:
                    logs_summaries = response['results']['logs']['tail']
                    for log_summary_line in logs_summaries:
                        key = (
                            log_summary_line['timestamp'],
                            log_summary_line['message']
                        )
                        if key not in seen_log_summaries:
                            log_summaries_dest.append(key)
                            seen_log_summaries.add(key)
            except KeyError:
                pass

            try:
                logs = response['results']['logs']['raw']
                for log_line in logs:
                    key = (
                        log_line['timestamp'],
                        log_line['level'],
                        log_line['message']
                    )
                    if key not in seen_logs:
                        level_constant = self._LOG_LEVELS[log_line['level']]
                        newmsg = f"[SERVER] {log_line['message']}"
                        seen_logs.add(key)
                        if level_constant >= raw_log_level:
                            self.logger.log(level_constant, newmsg)
            except KeyError:
                pass

            try:
                if intermediate_items_dest is not None:
                    for step_items in response['results']['full']:
                        for intermediate_item in step_items['items']:
                            ii_id = intermediate_item['_meta']['id']
                            if ii_id not in seen_intermediate_item_ids:
                                seen_intermediate_item_ids.add(ii_id)
                                intermediate_items_dest.append(intermediate_item)
            except KeyError:
                continue

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
            url_or_urls: The starting URL or a list of starting URLs
            item_template: the item template described above
            per_page: 'one'|'many'|'auto' - defaults to 'auto'.  Set this to 'one' if each URL has only a single item.  Set this to 'many' if each URL should yield multiple items
            max_pages: enable pagination from the given URL.  Defaults to one page only.
            limit: limit the number of items yielded by this step
        """
        return self._workflow(url_or_urls).extract(*args, **kwargs)

    def crawl(self, url_or_urls, *args, **kwargs):
        """Crawl for URLs from a starting point.

        A query can be either a prompt for the AI, or a URL pattern.

        A prompt for the AI is a plain language description fo the types of
        URLs you are looking for.

        A URL pattern is a valid URL with at least one * in it. URLs matching
        this pattern will be returned.

        Args:
            query: A plain language prompt, or a URL pattern
            pull: If true, the page contents will be pulled and returned
            limit: limit the number of items yielded by this step
        """
        return self._workflow(url_or_urls).crawl(*args, **kwargs)

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
