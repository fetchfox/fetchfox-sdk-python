import pytest
import responses
import json
import os
import os.path
import pathlib
from responses.matchers import json_params_matcher

from fetchfox_sdk import FetchFox

# Get directory containing the current script
SCRIPT_DIR = pathlib.Path(__file__).parent.resolve()
# Build path relative to it
MOCKS_DIR = (SCRIPT_DIR / "mocks").resolve()

@pytest.fixture
def host(request):
    return request.config.getoption("--host")

@pytest.fixture
def api_key(request):
    return request.config.getoption("--api-key")

@pytest.fixture
def fox_sdk(host, api_key):
    """Create SDK instance configured for testing."""
    if host == "mock":
        return FetchFox(api_key="test_key", host="http://127.0.0.1")

    if not api_key:
        pytest.fail("API key required when testing against real server")

    return FetchFox(api_key=api_key, host=host)

@pytest.fixture
def maybe_mock_responses(host):
    """Conditionally apply response mocking."""
    if host == "mock":
        with responses.RequestsMock() as rsps:
            yield rsps
    else:
        yield None

def test_one_step_flow__extract(fox_sdk, maybe_mock_responses, capsys):
    # Create
    city_pages = fox_sdk \
        .workflow("https://locations.traderjoes.com/pa/") \
        .extract(
            item_template = {
                "url": "Find me all the URLs for the city directories"
            }
        )

    # Setup mocks
    if maybe_mock_responses is not None:
        with open(os.path.join(MOCKS_DIR,"test_one_step_flow__extract.json")) as f:
            mocks = json.load(f)

        for mock in mocks:
            maybe_mock_responses.add(
                getattr(responses, mock['request']['method']),
                f"{fox_sdk.base_url}{mock['request']['url']}",
                json=mock['response']['json'],
                status=mock['response']['status_code'],
                match=[
                    json_params_matcher(mock['request']['json_data'])
                ] if mock['request']['json_data'] else []
            )

    # Run the function under test
    # In this case, we trigger workflow execution by materializing the results
    list_of_city_pages = list(city_pages)


    # Assert against real backend (should be true when mocking too):
    assert isinstance(list_of_city_pages, list)
    assert len(list_of_city_pages) > 2
    assert "traderjoes.com" in list_of_city_pages[0]['url']

    # Assert against the mock, where we have more specific responses handy
    if maybe_mock_responses:
        #TODO: assertions about the calls made?

        # There may be variation in e.g. the ordering when we're making real
        # requests, but in this mock, we know exactly how it will appear.
        expected_list_of_city_pages = [
            {'url': 'https://locations.traderjoes.com/pa/ardmore/'},
            {'url': 'https://locations.traderjoes.com/pa/berwyn/'},
            {'url': 'https://locations.traderjoes.com/pa/camp-hill/'},
            {'url': 'https://locations.traderjoes.com/pa/jenkintown/'},
            {'url': 'https://locations.traderjoes.com/pa/king-of-prussia/'},
            {'url': 'https://locations.traderjoes.com/pa/media/'},
            {'url': 'https://locations.traderjoes.com/pa/north-wales/'},
            {'url': 'https://locations.traderjoes.com/pa/philadelphia/'},
            {'url': 'https://locations.traderjoes.com/pa/pittsburgh/'},
            {'url': 'https://locations.traderjoes.com/pa/state-college/'},
            {'url': 'https://locations.traderjoes.com/pa/wayne/'}
        ]
        assert list_of_city_pages == expected_list_of_city_pages
        assert json.loads(maybe_mock_responses.calls[0].request.body) == city_pages.to_dict()

    # Additional assertions or debug only if hitting a real backend:
    if maybe_mock_responses is None:
        with capsys.disabled():
            print("\n### Real Activity: ###")
            print(f"Extracted Data: {city_pages[0]}")
            print(f"Extracted Data: {city_pages[1]}")
            print("### End Real Activity ###\n")

def test_one_step_flow__extract(fox_sdk, maybe_mock_responses, capsys):
    # Create
    city_pages = fox_sdk \
        .workflow("https://locations.traderjoes.com/pa/") \
        .extract(
            item_template = {
                "url": "Find me all the URLs for the city directories"
            }
        )

    # Setup mocks
    if maybe_mock_responses is not None:
        with open(os.path.join(MOCKS_DIR,"test_one_step_flow__extract.json")) as f:
            mocks = json.load(f)

        for mock in mocks:
            maybe_mock_responses.add(
                getattr(responses, mock['request']['method']),
                f"{fox_sdk.base_url}{mock['request']['url']}",
                json=mock['response']['json'],
                status=mock['response']['status_code'],
                match=[
                    json_params_matcher(mock['request']['json_data'])
                ] if mock['request']['json_data'] else []
            )

    # Run the function under test
    # In this case, we trigger workflow execution by materializing the results
    list_of_city_pages = list(city_pages)


    # Assert against real backend (should be true when mocking too):
    assert isinstance(list_of_city_pages, list)
    assert len(list_of_city_pages) > 2
    assert "traderjoes.com" in list_of_city_pages[0]['url']

    # Assert against the mock, where we have more specific responses handy
    if maybe_mock_responses:
        #TODO: assertions about the calls made?

        # There may be variation in e.g. the ordering when we're making real
        # requests, but in this mock, we know exactly how it will appear.
        expected_list_of_city_pages = [
            {'url': 'https://locations.traderjoes.com/pa/ardmore/'},
            {'url': 'https://locations.traderjoes.com/pa/berwyn/'},
            {'url': 'https://locations.traderjoes.com/pa/camp-hill/'},
            {'url': 'https://locations.traderjoes.com/pa/jenkintown/'},
            {'url': 'https://locations.traderjoes.com/pa/king-of-prussia/'},
            {'url': 'https://locations.traderjoes.com/pa/media/'},
            {'url': 'https://locations.traderjoes.com/pa/north-wales/'},
            {'url': 'https://locations.traderjoes.com/pa/philadelphia/'},
            {'url': 'https://locations.traderjoes.com/pa/pittsburgh/'},
            {'url': 'https://locations.traderjoes.com/pa/state-college/'},
            {'url': 'https://locations.traderjoes.com/pa/wayne/'}
        ]
        assert list_of_city_pages == expected_list_of_city_pages
        assert json.loads(maybe_mock_responses.calls[0].request.body) == city_pages.to_dict()

    # Additional assertions or debug only if hitting a real backend:
    if maybe_mock_responses is None:
        with capsys.disabled():
            print("\n### Real Activity: ###")
            print(f"Extracted Data: {city_pages[0]}")
            print(f"Extracted Data: {city_pages[1]}")
            print("### End Real Activity ###\n")

def test_setup_of_derived_flow__parent_has_results(fox_sdk, maybe_mock_responses, capsys):
    # Create first workflow
    city_pages = fox_sdk \
        .workflow("https://locations.traderjoes.com/pa/") \
        .extract(
            item_template = {
                "url": "Find me all the URLs for the city directories"
            }
        )

    # Setup mocks
    if maybe_mock_responses is not None:
        with open(os.path.join(MOCKS_DIR,"test_one_step_flow__extract.json")) as f:
            mocks = json.load(f)

        for mock in mocks:
            maybe_mock_responses.add(
                getattr(responses, mock['request']['method']),
                f"{fox_sdk.base_url}{mock['request']['url']}",
                json=mock['response']['json'],
                status=mock['response']['status_code'],
                match=[
                    json_params_matcher(mock['request']['json_data'])
                ] if mock['request']['json_data'] else []
            )

    # Run the function under test
    # In this case, we trigger workflow execution by materializing the results
    list_of_city_pages = list(city_pages)
    assert city_pages._results is not None

    # Now, when we make flows derived from city pages, they should be initialized
    # with the results

    store_info = city_pages.extract(
        item_template = {
            "store_address": "find me the address of the store",
            "store_number": "Find me the number of the store (it's in parentheses)",
            "store_phone": "Find me the phone number of the store"
            }
    )

    assert store_info._workflow['steps'][0]['name'] == "const"
    assert store_info._workflow['steps'][0]['args']['items'] == list_of_city_pages
    # If these are true, we have (correctly) used the executed parent workflow
    # results for the initial step of the derived workflow - that means that
    # the already executed step will not be re-executed.
    # Contrast to test_setup_of_derived_flow__parent_never_ran

def test_setup_of_derived_flow__parent_never_ran(fox_sdk, maybe_mock_responses, capsys):
    # Create first workflow
    city_pages = fox_sdk \
        .workflow("https://locations.traderjoes.com/pa/") \
        .extract(
            item_template = {
                "url": "Find me all the URLs for the city directories"
            }
        )

    # In this case, we don't ever run the parent workflow
    assert city_pages._results is None

    # Now, when we make flows derived from city pages, they should be initialized
    # as workflows extending the existing steps

    store_info = city_pages.extract(
        item_template = {
            "store_address": "find me the address of the store",
            "store_number": "Find me the number of the store (it's in parentheses)",
            "store_phone": "Find me the phone number of the store"
            }
    )

    assert len(store_info._workflow['steps']) == 3

    assert (
        store_info._workflow['steps'][0]['args']['items']
        ==
        [{'url': 'https://locations.traderjoes.com/pa/'}]
    )

    # If these are true, we have (correctly) extended the parent workflow
    # which means that, when something does require execution,
    # we won't be missing any steps / consts.
    # Contrast to test_setup_of_derived_flow__parent_has_results

def test_register_workflow(fox_sdk, maybe_mock_responses, capsys):
    # Create
    workflow = fox_sdk.workflow().init("https://example.com")

    # Setup mocks
    if maybe_mock_responses is not None:
        maybe_mock_responses.add(
            responses.POST,
            f"{fox_sdk.base_url}workflows",
            json={"id": "wf_123"},
            status=200
        )

    # Run the function under test
    workflow_id = fox_sdk.register_workflow(workflow)

    # Assert against real backend (should be true when mocking too):
    assert workflow_id is not None
    assert isinstance(workflow_id, str)
    assert  len(workflow_id) > 4 #just something

    # Assert against the mock, where we have more specific responses handy
    if maybe_mock_responses:
        assert workflow_id == "wf_123"
        assert len(maybe_mock_responses.calls) == 1
        assert json.loads(maybe_mock_responses.calls[0].request.body) == workflow.to_dict()

    # Additional assertions or debug only if hitting a real backend:
    if maybe_mock_responses is None:
        with capsys.disabled():
            print("\n### Real Activity: ###")
            print(f"Registered Real Workflow: {workflow_id}")
            print("### End Real Activity ###\n")


def test_run_workflow(fox_sdk):
    """Success implies register_workflow is fine too"""
    workflow = Workflow().init("https://example.com")

    with responses.RequestsMock() as rsps:
        # Mock workflow registration
        rsps.add(
            responses.POST,
            f"{fox_sdk.base_url}workflows",
            json={"id": "wf_123"},
            status=200
        )

        # Mock workflow run
        rsps.add(
            responses.POST,
            f"{fox_sdk.base_url}workflows/wf_123/run",
            json={"jobId": "job_456"},
            status=200
        )

        job_id = fox_sdk._run_workflow(workflow=workflow)
        assert job_id == "job_456"
        assert len(rsps.calls) == 2

def test_await_job_completion(fox_sdk):
    with responses.RequestsMock() as rsps:
        # First call returns not done
        rsps.add(
            responses.GET,
            f"{fox_sdk.base_url}jobs/job_123",
            json={"done": False},
            status=200
        )

        # Second call returns done with results
        rsps.add(
            responses.GET,
            f"{fox_sdk.base_url}jobs/job_123",
            json={
                "done": True,
                "results": {
                    "items": [{"name": "test", "_internal": "value"}]
                }
            },
            status=200
        )

        results = fox_sdk.await_job_completion("job_123", poll_interval=0.1)
        assert results == [{"name": "test"}]
        assert len(rsps.calls) == 2

def test_extract__with_template(fox_sdk):
    template = {"name": "What's the name?"}

    with responses.RequestsMock() as rsps:
        # Mock workflow registration
        rsps.add(
            responses.POST,
            f"{fox_sdk.base_url}workflows",
            json={"id": "wf_123"},
            status=200
        )

        # Mock workflow run
        rsps.add(
            responses.POST,
            f"{fox_sdk.base_url}workflows/wf_123/run",
            json={"jobId": "job_456"},
            status=200
        )

        # Mock job completion
        rsps.add(
            responses.GET,
            f"{fox_sdk.base_url}jobs/job_456",
            json={
                "done": True,
                "results": {
                    "items": [{"name": "Test Item"}]
                }
            },
            status=200
        )

        results = fox_sdk.extract("https://example.com", item_template=template)
        assert results == [{"name": "Test Item"}]
        assert len(rsps.calls) == 3

def test_plan_extraction_from_prompt(fox_sdk):
   url = "https://earthquake.usgs.gov/earthquakes/map/?extent=-89.71968,-79.80469&extent=89.71968,479.88281"
   instruction = "Grab me the magnitude, location, and time of all the earthquakes listed on this page."

   with responses.RequestsMock() as rsps:
       # Mock the fetch request
       rsps.add(
           responses.GET,
           f"{fox_sdk.base_url}fetch?{url}",
           json={
               "title": "Latest Earthquakes",
               "screenshot": "https://ffcloud.s3.amazonaws.com/fetchfox-screenshots/3v2ek2o503/https-earthquake-usgs-gov-earthquakes-map-extent-89-71968-79-80469-extent-89-71968-479-88281.png",
               "html": "https://ffcloud.s3.amazonaws.com/fetchfox-htmls/3v2ek2o503/https-earthquake-usgs-gov-earthquakes-map-extent-89-71968-79-80469-extent-89-71968-479-88281.html",
               "sec": 10.053
           },
           status=200
       )

       # Mock the plan request
       expected_plan = {
           "steps": [
               {
                   "name": "const",
                   "args": {
                       "items": [
                           {
                               "url": url
                           }
                       ],
                       "maxPages": 1
                   }
               },
               {
                   "name": "extract",
                   "args": {
                       "questions": {
                           "magnitude": "What is the magnitude of this earthquake?",
                           "location": "What is the location of this earthquake?",
                           "time": "What is the time of this earthquake?"
                       },
                       "single": True,
                       "maxPages": 1
                   }
               }
           ],
           "options": {
               "tokens": {},
               "user": None,
               "limit": None,
               "publishAllSteps": False
           },
           "name": "USGS Earthquake Details Scraper",
           "description": "Scrape earthquake details including magnitude, location, and time from the USGS earthquake map."
       }

       rsps.add(
           responses.POST,
           f"{fox_sdk.base_url}plan/from-prompt",
           json=expected_plan,
           status=200,
           match=[
               responses.matchers.json_params_matcher({
                   "prompt": instruction,
                   "urls": [url],
                   "html": "https://ffcloud.s3.amazonaws.com/fetchfox-htmls/3v2ek2o503/https-earthquake-usgs-gov-earthquakes-map-extent-89-71968-79-80469-extent-89-71968-479-88281.html"
               })
           ]
       )

       workflow = fox_sdk._plan_extraction_from_url_and_prompt(url, instruction)

       # Verify both requests were made
       assert len(rsps.calls) == 2

       # Verify the workflow was created correctly
       assert workflow.to_dict() == expected_plan

def test_extract__with_prompt(fox_sdk):
    raise NotImplementedError()

def test_workflow_from_json(fox_sdk):
    raise NotImplementedError()