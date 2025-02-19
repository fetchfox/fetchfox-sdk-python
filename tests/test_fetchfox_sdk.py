import pytest
import responses
import json
from fetchfox_sdk import FetchFoxSDK

# Test constants
API_KEY = "test_api_key_local"
TEST_HOST = "http://127.0.0.1:8081"

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
        return FetchFoxSDK(api_key="test_key", host="http://127.0.0.1")

    if not api_key:
        pytest.fail("API key required when testing against real server")

    return FetchFoxSDK(api_key=api_key, host=host)

@pytest.fixture
def maybe_mock_responses(host):
    """Conditionally apply response mocking."""
    if host == "mock":
        with responses.RequestsMock() as rsps:
            yield rsps
    else:
        yield None

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

        job_id = fox_sdk.run_workflow(workflow=workflow)
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

       workflow = fox_sdk._plan_extraction_from_prompt(url, instruction)

       # Verify both requests were made
       assert len(rsps.calls) == 2

       # Verify the workflow was created correctly
       assert workflow.to_dict() == expected_plan

def test_extract__with_prompt(fox_sdk):
    raise NotImplementedError()

def test_find_urls(fox_sdk):
    raise NotImplementedError()

def test_workflow_from_json(fox_sdk):
    raise NotImplementedError()