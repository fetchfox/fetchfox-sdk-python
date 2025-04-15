from fastmcp import FastMCP
from fetchfox_sdk import FetchFox

# ADD API KEY TO CLIENT INIT FetchFox(api_key="YOUR KEY")
fox = FetchFox()

mcp = FastMCP("FetchFox MCP", dependencies=["fetchfox_sdk"])

@mcp.tool()
def extract(url: str, item_template: dict) -> list:
    """Extract data from a URL and return the results"""
    items = fox.extract(url, item_template)
    
    results = []
    for item in items:
        results.append(item.to_dict())
    
    return results

@mcp.tool()
def crawl(url: str) -> list:
    """Crawl for URLs from a starting point and return the results"""
    urls = fox.crawl(url)
    
    results = []
    for url in urls:
        results.append(url)
    
    return results

@mcp.prompt()
def scrape() -> str:
    """Scrape a URL and return the results"""
    return 'You must provide fields to scrape with a corresponding question for the field in the format of a dictionary.'
