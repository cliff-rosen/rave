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
    LOG_FORMAT,
    TAVILY_API_KEY
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
    create_kb_update_prompt,
    ChecklistItem,
    ChecklistResponse,
    KnowledgeNugget,
    KBUpdateResponse
)

class State(TypedDict):
    """State for the RAVE workflow"""
    messages: Annotated[list, add_messages]
    question: str
    improved_question: str
    scored_checklist: List[Dict[str, Any]]
    answer: str
    query_history: List[str]
    search_results: List[Dict[str, Any]]
    current_query: str
    knowledge_base: List[KnowledgeNugget]
    cancelled: bool

def validate_state(state: State) -> bool:
    """Validate the state before processing"""
    if not state["question"]:
        print("No question provided")
        return False
    return True

def improve_question(state: State, writer: StreamWriter, config: Dict[str, Any]) -> AsyncIterator[Dict[str, Any]]:
    """Improve the question for clarity and completeness"""
    print("improve_question")
    if not validate_state(state):
        writer({"msg": "Error: No question provided"})
        return {}
    
    llm = ChatOpenAI(model=config["configurable"]["question_model"])
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

def generate_scored_checklist(state: State, writer: StreamWriter, config: Dict[str, Any]) -> AsyncIterator[Dict[str, Any]]:
    """Generate a checklist of requirements for a well-formed answer"""
    if not validate_state(state):
        writer({"msg": "Error: No question provided"})
        return {}
    
    llm = ChatOpenAI(model=config["configurable"]["checklist_model"])
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

def generate_query(state: State, writer: StreamWriter, config: Dict[str, Any]) -> AsyncIterator[Dict[str, Any]]:
    """Generate a search query based on the question and checklist"""
    if not validate_state(state):
        writer({"msg": "Error: No question provided"})
        return {}
    
    llm = ChatOpenAI(model=config["configurable"]["query_model"])
    query_generator_prompt = create_query_generator_prompt()
    
    try:
        writer({"msg": "Generating search query..."})
        formatted_prompt = query_generator_prompt.format(
            question=state["improved_question"],
            checklist=json.dumps(state["scored_checklist"]),
            query_history=json.dumps(state.get("query_history", []))
        )
        
        query_response = llm.invoke(formatted_prompt)
        # Strip any quotes from the query
        new_query = query_response.content.strip().strip('"\'')
        
        # Update query history
        query_history = state.get("query_history", [])
        query_history.append(new_query)
        
        writer({"msg": "Search query generated successfully"})
        return {
            "current_query": new_query,
            "query_history": query_history
        }
        
    except Exception as e:
        writer({"msg": f"Error generating search query: {str(e)}"})
        return {}

def search(state: State, writer: StreamWriter) -> AsyncIterator[Dict[str, Any]]:
    """Perform a search using the generated query"""
    if not validate_state(state):
        writer({"msg": "Error: No question provided"})
        return {}
    
    try:
        writer({"msg": "Performing search..."})
        
        # Debug: Check API key
        if not TAVILY_API_KEY:
            writer({"msg": "Error: TAVILY_API_KEY not set"})
            return {}
        
        # Initialize Tavily search
        search = TavilySearchResults(api_key=TAVILY_API_KEY, max_results=MAX_SEARCH_RESULTS)
        
        # Get the current query from state
        current_query = state.get("current_query")
        if not current_query:
            writer({"msg": "Error: No search query available"})
            return {}
        else:
            writer({"msg": "using current_query: " + current_query})
        
        
        # Perform the search
        search_results = search.invoke(current_query)
        # test_query = "Latest news and updates in technology along with their sources and significance"
        # search_results = search.invoke(test_query)
        
        # Debug: Print raw search results
        # print("Raw search results:", search_results)
        # print("Type of search results:", type(search_results))
        
        if not search_results:
            writer({"msg": "Warning: No search results found. The answer will be generated without external sources."})
            return {"search_results": []}
        
        writer({"msg": "Search completed successfully"})
        return {"search_results": search_results}
        
    except Exception as e:
        writer({"msg": f"Error performing search: {str(e)}"})
        return {}

def generate_answer(state: State, writer: StreamWriter, config: Dict[str, Any]) -> AsyncIterator[Dict[str, Any]]:
    """Generate an answer to the improved question in markdown format"""
    if not validate_state(state):
        writer({"msg": "Error: No question provided"})
        return {}
    
    llm = ChatOpenAI(model=config["configurable"]["answer_model"])
    answer_prompt = create_direct_answer_prompt()
    
    try:
        writer({"msg": "Generating answer ..."})
        # Use the improved question if available, otherwise use the original
        question_to_use = state.get("improved_question", state["question"])
        
        # Get checklist and knowledge base
        checklist = state.get("scored_checklist", [])
        knowledge_base = state.get("knowledge_base", [])
        
        # Format the prompt with all necessary information and markdown instruction
        formatted_prompt = answer_prompt.format(
            question=question_to_use,
            checklist=json.dumps([item["item_to_score"] for item in checklist]),
            knowledge_base=json.dumps([nugget.dict() for nugget in knowledge_base]),
            format_instructions="Please format your answer in markdown, using appropriate headings, lists, and formatting to make the information clear and well-structured."
        )
        
        answer = llm.invoke(formatted_prompt)
        writer({"msg": "Answer generated successfully"})
        
        return {"answer": answer.content}
        
    except Exception as e:
        writer({"msg": f"Error generating answer: {str(e)}"})
        return {}

def score_answer(state: State, writer: StreamWriter, config: Dict[str, Any]) -> AsyncIterator[Dict[str, Any]]:
    """Score the answer against the checklist requirements"""
    if not validate_state(state):
        writer({"msg": "Error: No question provided"})
        return {}
    
    llm = ChatOpenAI(model=config["configurable"]["scoring_model"])
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

def update_knowledge_base(state: State, writer: StreamWriter, config: Dict[str, Any]) -> AsyncIterator[Dict[str, Any]]:
    """Update the knowledge base with new information from search results"""
    if not validate_state(state):
        writer({"msg": "Error: No question provided"})
        return {}
    
    llm = ChatOpenAI(model=config["configurable"]["kb_model"])
    kb_update_prompt = create_kb_update_prompt()
    parser = PydanticOutputParser(pydantic_object=KBUpdateResponse)
    
    try:
        writer({"msg": "Updating knowledge base..."})
        
        # Get current knowledge base and search results
        current_kb = state.get("knowledge_base", [])
        search_results = state.get("search_results", [])
        
        if not search_results:
            writer({"msg": "No new search results to incorporate"})
            return {"knowledge_base": current_kb}
        
        # Format the prompt with current KB and new search results
        formatted_prompt = kb_update_prompt.format(
            question=state["improved_question"],
            current_kb=json.dumps([nugget.dict() for nugget in current_kb]),
            search_results=json.dumps(search_results)
        )
        
        # Get LLM's analysis of how to update the KB
        kb_update_response = llm.invoke(formatted_prompt)
        
        # Debug: Print raw response
        print("Raw KB update response:", kb_update_response.content)
        
        try:
            # Parse the response
            update_data = parser.parse(kb_update_response.content)
            
            # Update the knowledge base
            updated_kb = current_kb.copy()
            
            # Process updated nuggets
            for update in update_data.updated_nuggets:
                # Find the existing nugget
                existing_nugget = next((n for n in updated_kb if n.nugget_id == update.nugget_id), None)
                if existing_nugget:
                    # Update the nugget with new values
                    if update.content is not None:
                        existing_nugget.content = update.content
                    if update.confidence is not None:
                        existing_nugget.confidence = update.confidence
                    if update.conflicts_with is not None:
                        existing_nugget.conflicts_with = update.conflicts_with
            
            # Add new nuggets
            updated_kb.extend(update_data.new_nuggets)
            
            writer({"msg": "Knowledge base updated successfully"})
            return {"knowledge_base": updated_kb}
            
        except Exception as parse_error:
            print("Error parsing KB update:", str(parse_error))
            print("Response content:", kb_update_response.content)
            writer({"msg": f"Error parsing knowledge base update: {str(parse_error)}"})
            return {"knowledge_base": current_kb}
            
    except Exception as e:
        print("Error in KB update:", str(e))
        writer({"msg": f"Error updating knowledge base: {str(e)}"})
        return {"knowledge_base": current_kb}

def should_continue_searching(state: State, config: Dict[str, Any]) -> bool:
    """Check if we should continue searching based on checklist scores and max iterations"""
        
    checklist = state.get("scored_checklist", [])
    if not checklist:
        return False
    
    # Get current iteration count from query history
    current_iterations = len(state.get("query_history", []))
    max_iterations = config["configurable"]["max_iterations"]
    
    # Check if we've reached max iterations
    if current_iterations >= max_iterations:
        print("Max iterations reached")
        return False
    
    # Check if any item has a score less than the threshold
    return any(item.get("current_score", 0) < config["configurable"]["score_threshold"] for item in checklist)

TEST_MODE = False
def is_test_mode(state: State) -> bool:
    print("TEST_MODE: " + str(TEST_MODE))
    return {"improve_question": "new question"}

# Define the graph
graph_builder = StateGraph(State)


# Add nodes
graph_builder.add_node("improve_question", improve_question)
graph_builder.add_node("generate_scored_checklist", generate_scored_checklist)
graph_builder.add_node("generate_query", generate_query)
graph_builder.add_node("search", search)
graph_builder.add_node("update_knowledge_base", update_knowledge_base)
graph_builder.add_node("generate_answer", generate_answer)
graph_builder.add_node("score_answer", score_answer)

# Add edges
graph_builder.add_edge(START, "improve_question")
graph_builder.add_edge("improve_question", "generate_scored_checklist")
graph_builder.add_edge("generate_scored_checklist", "generate_query")
graph_builder.add_edge("generate_query", "search")
#graph_builder.add_edge("generate_query", END)
graph_builder.add_edge("search", "update_knowledge_base")
graph_builder.add_edge("update_knowledge_base", "generate_answer")
graph_builder.add_edge("generate_answer", "score_answer")
graph_builder.add_conditional_edges(
    "score_answer",
    should_continue_searching,
    {
        True: "generate_query",  # If scores < threshold, go back to generate_query
        False: END  # If all scores are above threshold, we're done
    }
)

# Compile the graph
compiled = graph_builder.compile()
graph = compiled 