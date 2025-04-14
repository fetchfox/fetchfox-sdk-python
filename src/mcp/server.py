from fastmcp import FastMCP
from fetchfox_sdk import FetchFox

fox = FetchFox()

mcp = FastMCP("FetchFox MCP", dependencies=["fetchfox_sdk"])

@mcp.tool()
def extract(url: str, keys_to_extraction_instructions: dict) -> list:
    """Extract data from a URL and return the results"""
    items = fox.extract(url, keys_to_extraction_instructions)
    
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
