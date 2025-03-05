import pytest
from fetchfox_sdk.workflow import Workflow

class FakeSDK:
    def nqprint(self,*args, **kwargs):
        print(*args,**kwargs)

def test_init():
    """Test basic initialization of workflow"""
    w = Workflow(FakeSDK())
    assert w._workflow

def test_init_step():
    """Test the init step configuration"""
    url = "https://example.com"
    w = Workflow(FakeSDK()).init(url)
    
    expected = {
        "steps": [{
            "name": "const",
            "args": {
                "items": [{"url": url}],
                "maxPages": 1 #TODO
            }
        }]
    }
    
    assert w.to_dict()['steps'] == expected['steps']

def test_extract():
    """This only uses the questions->item_template form, as it is the actual
    workflow.  The instruction/prompt flow is only a convenience, and produces
    a workflow of this form."""

    template = {"name": "What's the name?", "price": "What's the price?"}
    w = (
        Workflow(FakeSDK())
        .init("https://example.com")
        .extract(template)
    )

    # I want to default to single=False and maxPages=1 and limit=None
    
    assert len(w._workflow["steps"]) == 2
    assert w._workflow["steps"][1] == {
        "name": "extract",
        "args": {
            "limit": None,
            "questions": template,
            "single": False,
            "maxPages": 1
        }
    }

def test_limit():
    limit = 5
    w = (
        Workflow(FakeSDK())
        .init("https://example.com")
        .extract({"name": "What's the name?"})
        .limit(limit)
    )
    
    assert w.to_dict()['options']['limit'] == limit

def test_limit__cannot_be_set_twice():
    """Test that attempting to set limit twice raises ValueError"""
    w = (
        Workflow(FakeSDK())
        .init("https://example.com")
        .extract({"name": "What's the name?"})
        .limit(5)
    )

    with pytest.raises(ValueError):
        w.limit(10)

def test_filter():
    """Test filter step configuration"""
    instruction = "Exclude items over $100"
    w = (
        Workflow(FakeSDK())
        .init("https://example.com")
        .extract({"price": "What's the price?"})
        .filter(instruction)
    )

    assert len(w._workflow["steps"]) == 3
    assert w._workflow["steps"][2] == {
        "name": "filter",
        "args": {
            "query": instruction,
            "limit": None
        }
    }

def test_unique():
    """Test unique step configuration"""
    fields = ["url", "name"]
    w = (
        Workflow(FakeSDK())
        .init("https://example.com")
        .unique(fields)
    )

    assert len(w._workflow["steps"]) == 2
    assert w._workflow["steps"][1] == {
        "name": "unique",
        "args": {
            "fields": fields,
            "limit": None
        }
    }

def test_complex_chain():
    """Test a more complex chain of operations"""
    url = "https://example.com"
    template = {"name": "What's the name?", "price": "What's the price?"}
    limit = 10

    w = (
        Workflow(FakeSDK())
        .init(url)
        .extract(template)
        .limit(limit)
        #.unique("url")
    )
    
    expected = {
        "steps": [
            {
                "name": "const",
                "args": {
                    "items": [{"url": url}],
                    "maxPages": 1,
                }
            },
            {
                "name": "extract",
                "args": {
                    "questions": template,
                    "single": False,
                    "maxPages": 1,
                    "limit": None
                }
            }
        ]
    }
    
    actual = w.to_dict()
    assert actual["steps"] == expected["steps"]
    assert actual['options']['limit'] == limit

def test_all__steps_can_have_limit_parameter():
    """Test that each step type can have its own limit parameter"""
    w = (
        Workflow(FakeSDK())
        .init("https://example.com")
        .extract({"name": "What's the name?"}, limit=4)
        .filter("Exclude expensive items", limit=3)
        .unique(["name"], limit=2)
    )

    steps = w.to_dict()["steps"]
    assert len(steps) == 4
    assert steps[1]["args"]["limit"] == 4  # extract limit
    assert steps[2]["args"]["limit"] == 3  # filter limit
    assert steps[3]["args"]["limit"] == 2  # unique limit

def test_transform_type_steps__can_have_max_pages():
    """Test that max_pages parameter works for supported steps"""
    w = (
        Workflow(FakeSDK())
        .init("https://example.com")
        .extract({"name": "What's the name?"}, max_pages=4)
    )

    steps = w.to_dict()["steps"]
    assert steps[1]["args"]["maxPages"] == 4  # extract max_pages

def test_to_dict():
    """Test converting workflow to dictionary"""
    w = (
        Workflow(FakeSDK())
        .init("https://example.com")
        .extract({"name": "What's the name?"})
        .limit(5)
    )
    
    result = w.to_dict()
    assert "steps" in result
    assert "options" in result
    assert result["options"]["limit"] == 5
    assert len(result["steps"]) == 2


# TODO: More meaningful tests, pertain to validation that we might like to help
# users with:
#   - test_unique_requires_prior_data_producing_step: unique can't be first step
#   - test_filter_requires_prior_data_producing_step: similar to unique
#   - test_init_must_be_first: all workflows should start with init
#   - test_workflow_validation: when implemented, test that invalid workflows are caught
#       - missing required fields
#       - invalid step combinations
#       - steps in illogical order
#   - test_extract_requires_valid_template: ensure template is dict with string values
#   - Maximum instruction lengths?

# In terms of dev-experience, we should consider how problems are coming back from
# the API.  It may make more sense to design carefully, once, in the API, and then
# all the potential SDKs just have to pass sensible, descriptive errors
# faithfully back to the users