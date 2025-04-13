from typing import Annotated, Dict, Any, AsyncIterator, List, Optional, Iterator
from typing_extensions import TypedDict
from pydantic import BaseModel
import logging
from langgraph.graph import StateGraph, START, END
from langgraph.types import StreamWriter
import time

class State(TypedDict):
    topic: str
    joke: str


def generate_joke(state: State, writer: StreamWriter):
    writer({"custom_key": "Writing custom data while generating a joke"})
    time.sleep(1)
    writer({"custom_key": "Writing custom data while generating a joke"})    
    time.sleep(1)
    return {"joke": f"This is a joke about {state['topic']}"}


graph = (
    StateGraph(State)
    .add_node(generate_joke)
    .add_edge(START, "generate_joke")
    .add_edge("generate_joke", END)
    .compile()
)


for stream_mode, chunk in graph.stream(
    {"topic": "ice cream"},
    stream_mode=["updates", "custom"],
):
    print(f"Stream mode: {stream_mode}")
    print("chunk", chunk)
    print("\n")