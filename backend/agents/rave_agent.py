from typing import Annotated, Dict, Any, AsyncIterator, List, Optional, Iterator
from typing_extensions import TypedDict
from pydantic import BaseModel
import logging
import json
from datetime import datetime
import time
import random
import operator

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.prompts import ChatPromptTemplate

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import StreamWriter, Send

from ..config.settings import (
    DEFAULT_MODEL,
    MAX_ITERATIONS,
    SCORE_THRESHOLD,
    IMPROVEMENT_THRESHOLD,
    MAX_SEARCH_RESULTS,
    LOG_LEVEL,
    LOG_FORMAT
)

from .utils.prompts import (
    create_evaluator_prompt,
    create_gap_analyzer_prompt,
    create_query_generator_prompt,
    create_response_generator_prompt,
    create_direct_answer_prompt
)

# Set up logging
logging.basicConfig(
    level=LOG_LEVEL,
    format=LOG_FORMAT,
    handlers=[
        logging.FileHandler(f'rave_agent_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class State(TypedDict):
    """State for the RAVE workflow"""
    messages: Annotated[list, add_messages]
    question: str
    answer: str

def validate_state(state: State) -> bool:
    """Validate the state before processing"""
    if not state["question"]:
        logger.error("No question provided")
        return False
    return True

def generate_answer(state: State, writer: StreamWriter) -> AsyncIterator[Dict[str, Any]]:
    if not validate_state(state):
        return {"error": "Invalid state"}
    
    llm = ChatOpenAI(model=DEFAULT_MODEL)
    answer_prompt = create_direct_answer_prompt()
    
    try:
        writer({"msg": "Generating answer..."})
        # Format the messages and log them
        formatted_prompt = answer_prompt.format(question=state["question"])
        
        answer = llm.invoke(formatted_prompt)
        writer({"msg": "Answer generated successfully"})
        
        # Return only the updated portion of the state
        return {"answer": answer.content}
        
    except Exception as e:
        return {"error": str(e)}

# Define the graph
graph_builder = StateGraph(State)

# Add nodes
graph_builder.add_node("generate_answer", generate_answer)

# Add edges
graph_builder.add_edge(START, "generate_answer")
graph_builder.add_edge("generate_answer", END)

# Compile the graph
compiled = graph_builder.compile()
graph = compiled 