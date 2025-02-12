import pytest
import responses
import json
from fetchfox_sdk import FetchFoxSDK, Workflow

# Test constants
API_KEY = "test_api_key_local"
TEST_HOST = "http://127.0.0.1:8081"

@pytest.fixture
def fox_sdk():
    #TODO: right now, we don't hit this.  Just mocks.
    # We can parameterize this so as to highlight very clearly if the mocks
    # differ from the actual reponses, and also allow  the tests to run
    # without having a development server up
    return FetchFoxSDK(api_key=API_KEY, host=TEST_HOST)

def test_register_workflow(fox_sdk):
    workflow = Workflow().init("https://example.com")

    with responses.RequestsMock() as rsps:
        rsps.add(
            responses.POST,
            f"{fox_sdk.base_url}workflows",
            json={"id": "wf_123"},
            status=200
        )

        workflow_id = fox_sdk.register_workflow(workflow)
        assert workflow_id == "wf_123"
        assert len(rsps.calls) == 1
        assert json.loads(rsps.calls[0].request.body) == workflow.to_dict()

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

def test_extract__with_prompt(fox_sdk):
    raise NotImplementedError()

def test_find_urls(fod_sdk):
