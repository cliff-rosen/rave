from langchain_community.tools.tavily_search import TavilySearchResults
import os

os.environ["TAVILY_API_KEY"] = "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"

config = {"configurable": {"thread_id": "1"}}
tool = TavilySearchResults(max_results=2)
tools = [tool]
res = tool.invoke("What's a 'node' in LangGraph?", config)
print(res)