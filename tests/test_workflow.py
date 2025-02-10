import pytest
from fetchfox_sdk.workflow import Workflow

def test_init():
    """Test basic initialization of workflow"""
    w = Workflow()
    assert w._workflow

def test_init_step():
    """Test the init step configuration"""
    url = "https://example.com"
    w = Workflow().init(url)
    
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
        Workflow()
        .init("https://example.com")
        .extract(template)
    )
    
    assert len(w._workflow["steps"]) == 2
    assert w._workflow["steps"][1] == {
        "name": "extract",
        "args": {
            "questions": template,
            "single": True, #TODO
            "maxPages": 1 #TODO
        }
    }

def test_find_urls():
    instruction = "Find all product links"
    w = (
        Workflow()
        .init("https://example.com")
        .find_urls(instruction)
    )
    
    assert len(w._workflow["steps"]) == 2
    assert w._workflow["steps"][1] == {
        "name": "crawl",
        "args": {
            "query": instruction,
            "maxPages": 1
        }
    }

def test_find_urls__with_max_pages():
    instruction = "Find all product links"
    max_pages = 5
    w = (
        Workflow()
        .init("https://example.com")
        .find_urls(instruction, max_pages=max_pages)
    )

    assert len(w._workflow["steps"]) == 2
    assert w._workflow["steps"][1] == {
        "name": "crawl",
        "args": {
            "query": instruction,
            "maxPages": max_pages
        }
    }

def test_limit():
    limit = 5
    w = (
        Workflow()
        .init("https://example.com")
        .extract({"name": "What's the name?"})
        .limit(limit)
    )
    
    assert w.to_dict()['options']['limit'] == limit

#TODO: test behavior when limit is redefined, expect error raised?

def test_unique():
    """Test unique configuration"""
    w = (
        Workflow()
        .init("https://example.com")
        .find_urls("Find product links")
        .unique("url")
    )
    
    assert w._options.get("uniqueBy") == "url"

def test_complex_chain():
    """Test a more complex chain of operations"""
    url = "https://example.com"
    find_urls_instructions = "Find product links"
    template = {"name": "What's the name?", "price": "What's the price?"}
    limit = 10

    w = (
        Workflow()
        .init(url)
        .find_urls(find_urls_instructions)
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
                    "maxPages": 1
                }
            },
            {
                "name": "crawl",
                "args": {
                    "query": find_urls_instructions,
                    "maxPages": 1
                }
            },
            {
                "name": "extract",
                "args": {
                    "questions": template,
                    "single": True, #TODO
                    "maxPages": 1
                }
            }
        ]
    }
    
    actual = w.to_dict()
    assert actual["steps"] == expected["steps"]
    assert actual['options']['limit'] == limit

def test_from_json():
    """Test creating workflow from JSON"""
    json_str = '''
    {
        "steps": [
            {
                "name": "const",
                "args": {
                    "items": [{"url": "https://example.com"}],
                    "maxPages": 1
                }
            },
            {
                "name": "extract",
                "args": {
                    "questions": {"name": "What's the name?"},
                    "single": true,
                    "maxPages": 1
                }
            }
        ],
        "options": {
            "limit": 5
        }
    }
    '''
    
    w = Workflow.from_json(json_str)
    assert len(w._workflow["steps"]) == 2
    assert w._workflow["options"]["limit"] == 5

def test_to_dict():
    """Test converting workflow to dictionary"""
    w = (
        Workflow()
        .init("https://example.com")
        .extract({"name": "What's the name?"})
        .limit(5)
    )
    
    result = w.to_dict()
    assert "steps" in result
    assert "options" in result
    assert result["options"]["limit"] == 5
    assert len(result["steps"]) == 2