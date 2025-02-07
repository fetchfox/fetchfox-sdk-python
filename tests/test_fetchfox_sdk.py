import pytest
import responses
import json
from fetchfox_sdk import FetchFoxSDK

# Test constants
API_KEY = "test_api_key_local"
TEST_HOST = "http://127.0.0.1:8081"

@pytest.fixture
def sdk():
    return FetchFoxSDK(api_key=API_KEY, host=TEST_HOST)

@pytest.fixture
def mock_responses():
    with responses.RequestsMock() as rsps:
        yield rsps

def test_init():
    """Test SDK initialization"""
    sdk = FetchFoxSDK(api_key=API_KEY)
    assert sdk.api_key == API_KEY
    assert sdk.host == "https://fetchfox.ai"
    assert sdk.headers == {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer: {API_KEY}'
    }

    # Test custom host
    custom_host = "https://custom.fetchfox.ai/"
    sdk = FetchFoxSDK(api_key=API_KEY, host=custom_host)
    assert sdk.host == "https://custom.fetchfox.ai"  # Should strip trailing slash

class TestCoreAPI:
    """Tests for core API functionality"""

    def test_create_workflow(self, sdk, mock_responses):
        """Test workflow creation"""
        workflow = {
            "steps": [
                {
                    "name": "const",
                    "args": {"items": [{"url": "https://example.com"}]}
                }
            ]
        }

        mock_responses.add(
            responses.POST,
            f"{TEST_HOST}/api/v2/workflows",
            json={"id": TEST_WORKFLOW_ID},
            status=200
        )

        workflow_id = sdk.create_workflow(workflow)
        assert workflow_id == TEST_WORKFLOW_ID

        # Check request
        assert len(mock_responses.calls) == 1
        assert mock_responses.calls[0].request.headers['Authorization'] == f'Bearer: {API_KEY}'
        assert json.loads(mock_responses.calls[0].request.body) == workflow

    def test_run_workflow(self, sdk, mock_responses):
        """Test running a workflow"""
        mock_responses.add(
            responses.POST,
            f"{TEST_HOST}/api/v2/workflows/{TEST_WORKFLOW_ID}/run",
            json={"jobId": TEST_JOB_ID},
            status=200
        )

        job_id = sdk.run_workflow(TEST_WORKFLOW_ID)
        assert job_id == TEST_JOB_ID

    def test_get_job_status(self, sdk, mock_responses):
        """Test getting job status"""
        status_response = {
            "done": True,
            "results": {
                "items": [{"data": "test"}]
            }
        }

        mock_responses.add(
            responses.GET,
            f"{TEST_HOST}/api/v2/jobs/{TEST_JOB_ID}",
            json=status_response,
            status=200
        )

        status = sdk.get_job_status(TEST_JOB_ID)
        assert status == status_response

    def test_await_job(self, sdk, mock_responses):
        """Test waiting for job completion"""
        # First call returns not done
        mock_responses.add(
            responses.GET,
            f"{TEST_HOST}/api/v2/jobs/{TEST_JOB_ID}",
            json={"done": False},
            status=200
        )

        # Second call returns done with results
        results = {"items": [{"data": "test"}]}
        mock_responses.add(
            responses.GET,
            f"{TEST_HOST}/api/v2/jobs/{TEST_JOB_ID}",
            json={"done": True, "results": results},
            status=200
        )

        # Use a small poll interval for testing
        job_results = sdk.await_job(TEST_JOB_ID, poll_interval=0.1)
        assert job_results == results

class TestConvenienceMethods:
    """Tests for high-level convenience methods"""

    def test_extract_with_instruction(self, sdk, mock_responses):
        """Test extraction using natural language instruction"""
        url = "https://example.com"
        instruction = "Get all the product prices"

        # Mock workflow creation
        mock_responses.add(
            responses.POST,
            f"{TEST_HOST}/api/v2/workflows",
            json={"id": TEST_WORKFLOW_ID},
            status=200
        )

        # Mock workflow run
        mock_responses.add(
            responses.POST,
            f"{TEST_HOST}/api/v2/workflows/{TEST_WORKFLOW_ID}/run",
            json={"jobId": TEST_JOB_ID},
            status=200
        )

        # Mock job completion
        results = {"items": [{"price": "$10.99"}]}
        mock_responses.add(
            responses.GET,
            f"{TEST_HOST}/api/v2/jobs/{TEST_JOB_ID}",
            json={"done": True, "results": results},
            status=200
        )

        extracted_data = sdk.extract(url=url, instruction=instruction)
        assert extracted_data == results["items"]

        # Verify the workflow structure
        created_workflow = json.loads(mock_responses.calls[0].request.body)
        assert len(created_workflow["steps"]) == 2
        assert created_workflow["steps"][0]["name"] == "const"
        assert created_workflow["steps"][0]["args"]["items"][0]["url"] == url
        assert created_workflow["steps"][1]["name"] == "extract"
        assert created_workflow["steps"][1]["args"]["questions"]["result"] == instruction

    def test_extract_with_template(self, sdk, mock_responses):
        """Test extraction using item template"""
        url = "https://example.com"
        template = {
            "price": "What is the product price?",
            "name": "What is the product name?"
        }

        # Mock API calls
        mock_responses.add(
            responses.POST,
            f"{TEST_HOST}/api/v2/workflows",
            json={"id": TEST_WORKFLOW_ID},
            status=200
        )

        mock_responses.add(
            responses.POST,
            f"{TEST_HOST}/api/v2/workflows/{TEST_WORKFLOW_ID}/run",
            json={"jobId": TEST_JOB_ID},
            status=200
        )

        results = {"items": [{"price": "$10.99", "name": "Test Product"}]}
        mock_responses.add(
            responses.GET,
            f"{TEST_HOST}/api/v2/jobs/{TEST_JOB_ID}",
            json={"done": True, "results": results},
            status=200
        )

        extracted_data = sdk.extract(url=url, item_template=template)
        assert extracted_data == results["items"]

        # Verify template was used correctly
        created_workflow = json.loads(mock_responses.calls[0].request.body)
        assert created_workflow["steps"][1]["args"]["questions"] == template

    def test_crawl(self, sdk, mock_responses):
        """Test URL crawling"""
        url = "https://example.com"
        instruction = "Find all product links"

        # Mock API calls
        mock_responses.add(
            responses.POST,
            f"{TEST_HOST}/api/v2/workflows",
            json={"id": TEST_WORKFLOW_ID},
            status=200
        )

        mock_responses.add(
            responses.POST,
            f"{TEST_HOST}/api/v2/workflows/{TEST_WORKFLOW_ID}/run",
            json={"jobId": TEST_JOB_ID},
            status=200
        )

        results = {"items": [{"url": "https://example.com/product1"}]}
        mock_responses.add(
            responses.GET,
            f"{TEST_HOST}/api/v2/jobs/{TEST_JOB_ID}",
            json={"done": True, "results": results},
            status=200
        )

        urls = sdk.crawl(url=url, instruction=instruction)
        assert urls == results["items"]

        # Verify crawl workflow structure
        created_workflow = json.loads(mock_responses.calls[0].request.body)
        assert len(created_workflow["steps"]) == 2
        assert created_workflow["steps"][0]["name"] == "const"
        assert created_workflow["steps"][1]["name"] == "crawl"
        assert created_workflow["steps"][1]["args"]["query"] == instruction

def test_error_handling(sdk, mock_responses):
    """Test error handling"""
    # Test API error
    mock_responses.add(
        responses.POST,
        f"{TEST_HOST}/api/v2/workflows",
        json={"error": "Invalid workflow"},
        status=400
    )

    with pytest.raises(requests.exceptions.HTTPError):
        sdk.create_workflow({"invalid": "workflow"})