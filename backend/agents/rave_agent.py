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
    create_response_generator_prompt
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

class Scorecard(BaseModel):
    """Criteria for evaluating responses"""
    completeness: float
    accuracy: float
    relevance: float
    clarity: float

class SearchHistory(BaseModel):
    """History of search queries and results"""
    queries: List[str]
    results: List[str]

class AttemptHistory(BaseModel):
    """History of previous attempts and their evaluations"""
    responses: List[str]
    scores: List[Scorecard]
    feedback: List[str]

class State(TypedDict):
    """State for the RAVE workflow"""
    messages: Annotated[list, add_messages]
    query: str
    scorecard: Scorecard
    search_history: SearchHistory
    attempt_history: AttemptHistory
    current_gaps: List[str]
    current_attempt: Optional[str]
    new_queries: List[str]
    search_results: List[str]

# Define the graph
graph_builder = StateGraph(State)

def validate_state(state: State) -> bool:
    """Validate the state before processing"""
    if not state["current_attempt"]:
        logger.error("No current attempt to evaluate")
        return False
    if not state["query"]:
        logger.error("No query provided")
        return False
    return True

def evaluator(state: State) -> AsyncIterator[Dict[str, Any]]:
    """Evaluate the current attempt against the scorecard"""
    if not validate_state(state):
        return {"error": "Invalid state"}
    
    llm = ChatOpenAI(model=DEFAULT_MODEL)
    evaluator_prompt = create_evaluator_prompt()
    
    try:
        # Format the messages and log them
        formatted_prompt = evaluator_prompt.format(current_attempt=state["current_attempt"])
        
        messages = [
            SystemMessage(content="You are an evaluator that assesses responses against a scorecard. Return a JSON object with 'score' and 'feedback' fields."),
            HumanMessage(content=formatted_prompt)
        ]
        
        evaluation = llm.invoke(messages)
        
        # Parse the JSON response
        eval_result = json.loads(evaluation.content)
        
        # Update the scorecard
        state["scorecard"] = Scorecard(**eval_result["score"])
        
        # Add to attempt history
        state["attempt_history"].responses.append(state["current_attempt"])
        state["attempt_history"].scores.append(state["scorecard"])
        state["attempt_history"].feedback.append(eval_result["feedback"])
        
        return state
        
    except Exception as e:
        return {"error": str(e)}

def gap_analyzer(state: State) -> AsyncIterator[Dict[str, Any]]:
    """Analyze gaps in the current attempt"""
    if not validate_state(state):
        return {"error": "Invalid state"}
    
    # Get the most recent feedback if it exists
    feedback = state["attempt_history"].feedback[-1] if state["attempt_history"].feedback else "Initial attempt"
    
    llm = ChatOpenAI(model=DEFAULT_MODEL)
    gap_analyzer_prompt = create_gap_analyzer_prompt()
    
    try:
        gaps = llm.invoke(gap_analyzer_prompt.format_messages(
            response=state["current_attempt"],
            feedback=feedback
        ))
        
        gap_list = gaps.content.split("\n")
        gap_list = [gap.strip() for gap in gap_list if gap.strip()]
        
        state["current_gaps"] = gap_list
        return state
        
    except Exception as e:
        return {"error": str(e)}

def query_generator(state: State) -> AsyncIterator[Dict[str, Any]]:
    """Generate new search queries based on gaps"""
    if not validate_state(state):
        return {"error": "Invalid state"}
    
    llm = ChatOpenAI(model=DEFAULT_MODEL)
    query_generator_prompt = create_query_generator_prompt()
    
    try:
        new_queries = llm.invoke(query_generator_prompt.format_messages(
            gaps=state["current_gaps"],
            query=state["query"],
            search_history=state["search_history"].queries
        ))
        
        # Clean up the query list
        query_list = [q.strip() for q in new_queries.content.split("\n") if q.strip()]
        query_list = [q for q in query_list if not q.startswith(("Gaps:", "Original Query:", "Previous Queries:", "With this information"))]
        
        # Update state
        state["new_queries"] = query_list
        state["search_history"].queries.extend(query_list)
        
        return state
        
    except Exception as e:
        return {"error": str(e)}

def search(state: State) -> AsyncIterator[Dict[str, Any]]:
    """Conduct search using the new queries"""
    if not validate_state(state):
        return {"error": "Invalid state"}
    
    # Get queries from the state
    queries = state.get("new_queries", [])
    if not queries:
        queries = state["current_gaps"]
    
    search_tool = TavilySearchResults(max_results=MAX_SEARCH_RESULTS)
    search_results = []
    
    try:
        for query in queries:
            results = search_tool.invoke(query)
            if isinstance(results, list):
                search_results.extend(results)
            else:
                search_results.append(results)
        
        # Update state
        state["search_results"] = search_results
        state["search_history"].results.extend(search_results)
        
        return state
        
    except Exception as e:
        return {"error": str(e)}

def response_generator(state: State) -> AsyncIterator[Dict[str, Any]]:
    """Generate a new improved response"""
    if not validate_state(state):
        return {"error": "Invalid state"}
    
    # Get search results from state
    search_results = state.get("search_results", [])
    if not search_results:
        search_results = state["current_gaps"]
    
    llm = ChatOpenAI(model=DEFAULT_MODEL)
    response_generator_prompt = create_response_generator_prompt()
    
    try:
        # Format search results for the prompt
        formatted_results = "\n".join([str(result) for result in search_results])
        
        new_response = llm.invoke(response_generator_prompt.format_messages(
            query=state["query"],
            new_info=formatted_results,
            previous_attempt=state["current_attempt"]
        ))
        
        # Update state
        state["current_attempt"] = new_response.content
        return state
        
    except Exception as e:
        return {"error": str(e)}

def should_continue(state: State) -> bool:
    """Determine if we should continue refining"""
    if not validate_state(state):
        return False

    logger.info("Checking continuation criteria")
    
    if len(state["attempt_history"].scores) >= MAX_ITERATIONS:  # Max iterations
        logger.info("Stopping: Maximum iterations reached")
        return False
    
    if len(state["attempt_history"].scores) > 1:
        last_score = state["attempt_history"].scores[-1]
        prev_score = state["attempt_history"].scores[-2]
        
        logger.info(f"Last score: {last_score}")
        logger.info(f"Previous score: {prev_score}")
        
        if (last_score.completeness >= SCORE_THRESHOLD and 
            last_score.accuracy >= SCORE_THRESHOLD and 
            last_score.relevance >= SCORE_THRESHOLD and 
            last_score.clarity >= SCORE_THRESHOLD):
            logger.info("Stopping: All scores above threshold")
            return False
            
        # Check for stagnation
        if (abs(last_score.completeness - prev_score.completeness) < IMPROVEMENT_THRESHOLD and
            abs(last_score.accuracy - prev_score.accuracy) < IMPROVEMENT_THRESHOLD and
            abs(last_score.relevance - prev_score.relevance) < IMPROVEMENT_THRESHOLD and
            abs(last_score.clarity - prev_score.clarity) < IMPROVEMENT_THRESHOLD):
            logger.info("Stopping: Stagnation detected")
            return False
    
    logger.info("Continuing refinement process")
    return True

def trace_transition(current_node: str, next_node: str, state: State) -> None:
    """Log the transition between nodes and relevant state information"""
    # Only log if we're actually transitioning to a new node
    if current_node != next_node:
        logger.info(f"\n{'='*50}")
        logger.info(f"TRANSITION: {current_node} -> {next_node}")
        logger.info(f"Current State:")
        logger.info(f"- Query: {state['query']}")
        logger.info(f"- Current Attempt: {state['current_attempt'][:200]}...")
        if state.get('scorecard'):
            logger.info(f"- Last Score: {state['scorecard']}")
        if state.get('current_gaps'):
            logger.info(f"- Current Gaps: {state['current_gaps']}")
        if state.get('new_queries'):
            logger.info(f"- New Queries: {state['new_queries']}")
        logger.info(f"{'='*50}\n")

# Add nodes
graph_builder.add_node("evaluator", evaluator)
graph_builder.add_node("gap_analyzer", gap_analyzer)
graph_builder.add_node("query_generator", query_generator)
graph_builder.add_node("search", search)
graph_builder.add_node("response_generator", response_generator)

# Add edges with validation and tracing

# add start node
graph_builder.add_edge(START, "evaluator")

graph_builder.add_conditional_edges(
    "evaluator",
    lambda state: (trace_transition("evaluator", "gap_analyzer", state) or True) and "error" not in state,
    {
        True: "gap_analyzer",
        False: END
    }
)

graph_builder.add_conditional_edges(
    "gap_analyzer",
    lambda state: (trace_transition("gap_analyzer", "query_generator", state) or True) and "error" not in state,
    {
        True: "query_generator",
        False: END
    }
)

graph_builder.add_conditional_edges(
    "query_generator",
    lambda state: (trace_transition("query_generator", "search", state) or True) and "error" not in state,
    {
        True: "search",
        False: END
    }
)

graph_builder.add_conditional_edges(
    "search",
    lambda state: (trace_transition("search", "response_generator", state) or True) and "error" not in state,
    {
        True: "response_generator",
        False: END
    }
)

graph_builder.add_conditional_edges(
    "response_generator",
    lambda state: (trace_transition("response_generator", "evaluator", state) or True) and "error" not in state and should_continue(state),
    {
        True: "evaluator",
        False: END
    }
)

# Compile the graph
compiled = graph_builder.compile()
graph = compiled 