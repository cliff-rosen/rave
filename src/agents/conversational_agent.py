from typing import Annotated, Dict, Any, AsyncIterator
from typing_extensions import TypedDict

from langchain_core.messages import ToolMessage
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, AIMessageChunk
from langchain_community.tools.tavily_search import TavilySearchResults

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver

import json

class State(TypedDict):
    messages: Annotated[list, add_messages]
    search_results: list[str]
    log: list[str]

def chatbot(state: State) -> AsyncIterator[Dict[str, Any]]:
    """Process the chat message and stream the response."""
    try:
        # Stream the response from the LLM
        return {"messages": llm_with_tools.invoke(state["messages"])}

    except Exception as e:
        print(f"Error in chatbot: {e}")  # Debug print
        raise

def update(state: State) -> AsyncIterator[Dict[str, Any]]:
    message = state["messages"][-1]
    print("\n*****************")
    print(message.pretty_print())
    print("*****************")
    return {"log": ["update"]}

def update2(state: State) -> AsyncIterator[Dict[str, Any]]:
    message = state["messages"][-1]
    print("\n*****************2")
    print(message.pretty_print())
    print("*****************")
    return {"log": ["update2"]}

# define resources
tool = TavilySearchResults(max_results=3)
tools = [tool]
llm = ChatOpenAI(
    model="gpt-4o-mini",
    streaming=True,
    temperature=0
)
llm_with_tools = llm.bind_tools(tools)
tool_node = ToolNode(tools=[tool])
memory = MemorySaver()

# define graph
graph_builder = StateGraph(State)

graph_builder.add_node("chatbot", chatbot)
graph_builder.add_node("update", update)
graph_builder.add_node("tools", tool_node)
graph_builder.add_node("update2", update2)

graph_builder.add_edge(START, "chatbot")
graph_builder.add_edge("chatbot", "update")
graph_builder.add_conditional_edges(
    "update",
    tools_condition,
)
graph_builder.add_edge("tools", "update2")
graph_builder.add_edge("update2", "chatbot")

compiled = graph_builder.compile(checkpointer=memory)
compiled.stream_mode = "messages"
graph = compiled
