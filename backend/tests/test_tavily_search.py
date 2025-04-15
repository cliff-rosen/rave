from langchain_community.tools.tavily_search import TavilySearchResults
from backend.config.settings import TAVILY_API_KEY, MAX_SEARCH_RESULTS

def test_tavily_search():
    print("\n=== Testing Tavily Search ===")
    print(f"Using API Key: {TAVILY_API_KEY[:5]}...{TAVILY_API_KEY[-5:]}")
    
    # Initialize search
    search = TavilySearchResults(api_key=TAVILY_API_KEY, max_results=MAX_SEARCH_RESULTS)
    
    # Test query
    test_query = "Latest news and updates in technology along with their sources and significance"
    print(f"\nTesting query: {test_query}")
    
    try:
        # Perform search
        results = search.invoke(test_query)
        print("\nRaw results:", results)
        print("Type of results:", type(results))
        
        if isinstance(results, list):
            print(f"\nNumber of results: {len(results)}")
            if results:
                print("\nFirst result:")
                print("Title:", results[0].get("title", "No title"))
                print("URL:", results[0].get("url", "No URL"))
                print("Content:", results[0].get("content", "No content")[:200] + "...")
        else:
            print("\nResults is not a list")
            
    except Exception as e:
        print(f"\nError during search: {str(e)}")

if __name__ == "__main__":
    test_tavily_search() 