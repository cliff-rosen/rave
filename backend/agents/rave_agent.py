from typing import Annotated, Dict, Any, AsyncIterator, List, Optional, Iterator, TypedDict
from pydantic import BaseModel, Field
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
from langchain_core.output_parsers import PydanticOutputParser

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
    create_direct_answer_prompt,
    create_question_improvement_prompt,
    create_checklist_prompt,
    create_scoring_prompt,
    ChecklistItem,
    ChecklistResponse
)

class State(TypedDict):
    """State for the RAVE workflow"""
    messages: Annotated[list, add_messages]
    question: str
    improved_question: str
    scored_checklist: List[Dict[str, Any]]
    answer: str

def validate_state(state: State) -> bool:
    """Validate the state before processing"""
    if not state["question"]:
        print("No question provided")
        return False
    return True

def improve_question(state: State, writer: StreamWriter) -> AsyncIterator[Dict[str, Any]]:
    """Improve the question for clarity and completeness"""
    if not validate_state(state):
        writer({"msg": "Error: No question provided"})
        return {}
    
    llm = ChatOpenAI(model=DEFAULT_MODEL)
    improvement_prompt = create_question_improvement_prompt()
    
    try:
        writer({"msg": "Improving question for clarity and completeness..."})
        formatted_prompt = improvement_prompt.format(question=state["question"])
        improved_question = llm.invoke(formatted_prompt)
        writer({"msg": "Question improved successfully"})
        
        return {"improved_question": improved_question.content}
        
    except Exception as e:
        writer({"msg": f"Error improving question: {str(e)}"})
        return {}

def generate_scored_checklist(state: State, writer: StreamWriter) -> AsyncIterator[Dict[str, Any]]:
    """Generate a checklist of requirements for a well-formed answer"""
    if not validate_state(state):
        writer({"msg": "Error: No question provided"})
        return {}
    
    llm = ChatOpenAI(model=DEFAULT_MODEL)
    parser = PydanticOutputParser(pydantic_object=ChecklistResponse)
    
    try:
        writer({"msg": "Generating answer requirements checklist..."})
        format_instructions = parser.get_format_instructions()
        checklist_prompt = create_checklist_prompt(format_instructions)
        formatted_prompt = checklist_prompt.format(
            question=state["improved_question"],
            format_instructions=format_instructions
        )
        checklist_response = llm.invoke(formatted_prompt)
        
        # Parse the response into checklist items
        parsed_response = parser.parse(checklist_response.content)
        checklist_items = [item.dict() for item in parsed_response.items]
        
        writer({"msg": "Checklist generated successfully"})
        return {"scored_checklist": checklist_items}
        
    except Exception as e:
        writer({"msg": f"Error generating checklist: {str(e)}"})
        return {}

def generate_answer(state: State, writer: StreamWriter) -> AsyncIterator[Dict[str, Any]]:
    """Generate an answer to the improved question"""
    if not validate_state(state):
        writer({"msg": "Error: No question provided"})
        return {}
    
    llm = ChatOpenAI(model=DEFAULT_MODEL)
    answer_prompt = create_direct_answer_prompt()
    
    try:
        writer({"msg": "Generating answer ..."})
        # Use the improved question if available, otherwise use the original
        question_to_use = state.get("improved_question", state["question"])
        formatted_prompt = answer_prompt.format(question=question_to_use)
        
        answer = llm.invoke(formatted_prompt)
        writer({"msg": "Answer generated successfully"})
        
        return {"answer": answer.content}
        
    except Exception as e:
        writer({"msg": f"Error generating answer: {str(e)}"})
        return {}

def score_answer(state: State, writer: StreamWriter) -> AsyncIterator[Dict[str, Any]]:
    """Score the answer against the checklist requirements"""
    if not validate_state(state):
        writer({"msg": "Error: No question provided"})
        return {}
    
    llm = ChatOpenAI(model=DEFAULT_MODEL)
    parser = PydanticOutputParser(pydantic_object=ChecklistResponse)
    
    try:
        writer({"msg": "Scoring answer against requirements..."})
        format_instructions = parser.get_format_instructions()
        scoring_prompt = create_scoring_prompt(format_instructions)
        formatted_prompt = scoring_prompt.format(
            question=state["improved_question"],
            answer=state["answer"],
            checklist=json.dumps([item["item_to_score"] for item in state["scored_checklist"]]),
            format_instructions=format_instructions
        )
        
        scoring_response = llm.invoke(formatted_prompt)
        parsed_response = parser.parse(scoring_response.content)
        
        # Convert Pydantic model back to dict format
        updated_checklist = [item.dict() for item in parsed_response.items]
        
        writer({"msg": "Answer scored successfully"})
        return {"scored_checklist": updated_checklist}
        
    except Exception as e:
        writer({"msg": f"Error scoring answer: {str(e)}"})
        return {}

# Define the graph
graph_builder = StateGraph(State)

# Add nodes
graph_builder.add_node("improve_question", improve_question)
graph_builder.add_node("generate_scored_checklist", generate_scored_checklist)
graph_builder.add_node("generate_answer", generate_answer)
graph_builder.add_node("score_answer", score_answer)

# Add edges
graph_builder.add_edge(START, "improve_question")
graph_builder.add_edge("improve_question", "generate_scored_checklist")
graph_builder.add_edge("generate_scored_checklist", "generate_answer")
graph_builder.add_edge("generate_answer", "score_answer")
graph_builder.add_edge("score_answer", END)

# Compile the graph
compiled = graph_builder.compile()
graph = compiled 