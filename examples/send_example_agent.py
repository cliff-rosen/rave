from typing import Annotated, Dict, Any, AsyncIterator, List, Optional, Iterator
from typing_extensions import TypedDict
from datetime import datetime
import time
import random
import operator

from langgraph.graph import StateGraph, START, END
from langgraph.types import StreamWriter, Send


class State(TypedDict):
    """State for the RAVE workflow"""
    question: str
    searches: Annotated[List[str], operator.add]


def step_1(state: State, writer: StreamWriter) -> Iterator[Dict[str, Any]]:
    return {"question": "improved question"}


def step_2(state: State, writer: StreamWriter) -> Iterator[Dict[str, Any]]:
    num = random.randint(1, 10)
    i = state["question"]
    for j in range(num):
        time.sleep(.5)
        writer({"msg": {"step": str(i), "count": str(j)}})
    return {"searches": ["search " + str(i)]}


def continue_to_step_2(state: State):
    return [Send("step_2", {"question": x}) for x in range(10)]


# Define the graph
graph_builder = StateGraph(State)

graph_builder.add_node("step_1", step_1)
graph_builder.add_node("step_2", step_2)
graph_builder.add_edge(START, "step_1")
graph_builder.add_conditional_edges(
    "step_1",
    continue_to_step_2,
    ["step_2"]
)

graph_builder.add_edge("step_2", END)

# Compile the graph without checkpointer for now
graph = graph_builder.compile()
