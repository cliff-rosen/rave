from typing import Annotated, Dict, Any, AsyncIterator, List, Optional, Iterator, TypedDict, Callable
from pydantic import BaseModel, Field
import logging
import json
from datetime import datetime
import time
import random
import operator
from serpapi import GoogleSearch

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_community.document_loaders import WebBaseLoader

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
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
    TAVILY_API_KEY,
    OPENAI_API_KEY,
    SERPAPI_API_KEY
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
    create_url_selection_prompt,
    ChecklistItem,
    ChecklistResponse,
    KnowledgeNugget,
    KBUpdateResponse,
    URLSelectionResponse
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
    scraped_content: List[str] 
    urls_to_scrape: List[str]
    current_query: str
    knowledge_base: List[KnowledgeNugget]
    cancelled: bool

def validate_state(state: State) -> bool:
    """Validate the state before processing"""
    if not state["question"]:
        print("No question provided")
        return False
    return True

def getModel(node_name: str, config: Dict[str, Any], writer: Optional[Callable] = None) -> ChatOpenAI:
    """Get the appropriate model for a given node.
    
    Args:
        node_name: The name of the node (e.g. 'question_model', 'answer_model')
        config: The configuration dictionary containing model settings
        writer: Optional callback for writing messages
        
    Returns:
        ChatOpenAI instance configured with the appropriate model
    """
    model_name = config["configurable"].get(node_name, DEFAULT_MODEL)
    
    # Special handling for non-chat models
    if model_name == "o1-pro":
        raise ValueError("o1-pro is not a chat model and cannot be used with chat completions")
    
    # Get model configuration
    from ..config.models import get_model_config
    model_config = get_model_config(model_name)
    
    # Create base model configuration
    chat_config = {
        "model": model_name,
        "api_key": OPENAI_API_KEY
    }
    
    # Only add temperature for models that support it
    if model_config.get("supports_temperature", True):
        chat_config["temperature"] = 0.0
    
    return ChatOpenAI(**chat_config)


### Nodes
def improve_question(state: State, writer: StreamWriter, config: Dict[str, Any]) -> AsyncIterator[Dict[str, Any]]:
    """Improve the question for clarity and completeness"""
    writer({"msg": "Improving question for clarity and completeness..."})
    
    if not validate_state(state):
        writer({"msg": "Error: No question provided"})
        return {}
    
    llm = getModel("question_model", config, writer)
    improvement_prompt = create_question_improvement_prompt()
    
    try:
        formatted_prompt = improvement_prompt.format(question=state["question"])
        improved_question = llm.invoke(formatted_prompt)
        writer({"msg": "Question improved successfully"})
        
        return {"improved_question": improved_question.content}
        
    except Exception as e:
        writer({"msg": f"Error improving question: {str(e)}"})
        return {}

def generate_scored_checklist(state: State, writer: StreamWriter, config: Dict[str, Any]) -> AsyncIterator[Dict[str, Any]]:
    """Generate a checklist of requirements for a well-formed answer"""
    writer({"msg": "Generating answer requirements checklist..."})
    
    if not validate_state(state):
        writer({"msg": "Error: No question provided"})
        return {}
    
    llm = getModel("checklist_model", config, writer)
    parser = PydanticOutputParser(pydantic_object=ChecklistResponse)
    
    try:
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
        
        writer({"msg": "Scorecard generated successfully"})
        return {"scored_checklist": checklist_items}
        
    except Exception as e:
        writer({"msg": f"Error generating checklist: {str(e)}"})
        return {}

def generate_query(state: State, writer: StreamWriter, config: Dict[str, Any]) -> AsyncIterator[Dict[str, Any]]:
    """Generate a search query based on the question and checklist"""
    writer({"msg": "Generating search query..."})
    
    if not validate_state(state):
        writer({"msg": "Error: No question provided"})
        return {}
    
    llm = getModel("query_model", config, writer)
    query_generator_prompt = create_query_generator_prompt()
    
    try:
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
    if writer:
        writer({"msg": "Performing search..."})
    
    if not validate_state(state):
        writer({"msg": "Error: No question provided"})
        return {}
    
    try:
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
        
        # Perform the search
        search_results = search.invoke(current_query)
        
        if not search_results:
            writer({"msg": "Warning: No search results found. The answer will be generated without external sources."})
            return {"search_results": []}
        
        if writer:
            writer({"msg": "Search completed successfully"})
        return {"search_results": search_results}
        
    except Exception as e:
        writer({"msg": f"Error performing search: {str(e)}"})
        return {}

def search2(state: State, writer: StreamWriter) -> AsyncIterator[Dict[str, Any]]:
    """Perform a search using SerpAPI instead of Tavily"""


    if writer:
        writer({"msg": "Performing search with SerpAPI..."})
    
    if not validate_state(state):
        writer({"msg": "Error: No question provided"})
        return {}
    
    try:
        # Debug: Check API key
        if not SERPAPI_API_KEY:
            writer({"msg": "Error: SERPAPI_API_KEY not set"})
            return {}
        
        # Get the current query from state
        current_query = state.get("current_query")
        if not current_query:
            writer({"msg": "Error: No search query available"})
            return {}
        
        # Perform the search using SerpAPI
        params = {
            "engine": "google",
            "q": current_query,
            "api_key": SERPAPI_API_KEY
        }
        
        search = GoogleSearch(params)
        results = search.get_dict()
        
        # Format results to match Tavily's format
        formatted_results = []
        if "organic_results" in results:
            for result in results["organic_results"]:
                formatted_results.append({
                    "title": result.get("title", ""),
                    "link": result.get("link", ""),
                    "snippet": result.get("snippet", ""),
                    "content": result.get("snippet", "")  # Using snippet as content since SerpAPI doesn't provide full content
                })
        
        if not formatted_results:
            if writer:
                writer({"msg": "Warning: No search results found. The answer will be generated without external sources."})
            return {"search_results": [1,2,3]}  
        
        if writer:
            writer({"msg": "Search completed successfully with SerpAPI"})
        return {"search_results": formatted_results}
        
    except Exception as e:
        if writer:
            writer({"msg": f"Error performing search with SerpAPI: {str(e)}"})
        return {}

def get_best_urls_from_search(state: State, writer: StreamWriter, config: Dict[str, Any]) -> AsyncIterator[Dict[str, Any]]:
    """Analyze search results to identify the most relevant URLs for answering the question"""

    if writer:
        writer({"msg": "Analyzing search results to identify relevant URLs..."})
    
    if not state.get("search_results"):
        if writer:
            writer({"msg": "No search results available to analyze"})
        print("No search results available to analyze")
        return {"urls_to_scrape": []}
    
    llm = getModel("url_model", config, writer)
    parser = PydanticOutputParser(pydantic_object=URLSelectionResponse)
    format_instructions = parser.get_format_instructions()
    url_selection_prompt = create_url_selection_prompt(format_instructions)
    
    try:
        formatted_prompt = url_selection_prompt.format(
            question=state["improved_question"],
            search_results=json.dumps(state["search_results"]),
            format_instructions=format_instructions
        )
        
        url_response = llm.invoke(formatted_prompt)

        # Parse the response using Pydantic
        try:
            parsed_response = parser.parse(url_response.content)
            # Return the full URLWithScore objects
            urls_to_scrape = parsed_response.urls
            
            if writer:
                writer({"msg": f"Selected {len(urls_to_scrape)} relevant URLs for scraping"})
            return {"urls_to_scrape": urls_to_scrape}
            
        except Exception as parse_error:
            writer({"msg": f"Error parsing URL selection response: {str(parse_error)}"})
            return {"urls_to_scrape": []}
            
    except Exception as e:
        writer({"msg": f"Error selecting URLs: {str(e)}"})
        return {"urls_to_scrape": []}

def scrape_urls(state: State, writer: StreamWriter, config: Dict[str, Any]) -> AsyncIterator[Dict[str, Any]]:
    """Scrape the URLs and return the content"""

    if writer:
        writer({"msg": "Scraping URLs..."})

    if not state.get("urls_to_scrape"):
        writer({"msg": "No URLs to scrape"})
        return {"scraped_content": []}
    
    # Extract URLs from URLWithScore objects
    urls_to_scrape = [url_obj.url for url_obj in state.get("urls_to_scrape")]

    docs = []
    for url in urls_to_scrape:
        try:
            # Configure WebBaseLoader with proper headers and timeouts
            loader = WebBaseLoader(
                web_paths=[url],
                requests_kwargs={
                    "headers": {
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                        "Accept-Language": "en-US,en;q=0.5",
                    },
                    "timeout": 10,  # 10 second timeout
                    "verify": True,  # Verify SSL certificates
                }
            )

            # Try to load the content with retries
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    print("--------------------------------")
                    print("attempt", attempt)
                    print("--------------------------------")
                    for doc in loader.lazy_load():
                        print("--------------------------------")
                        print(doc)
                        print("--------------------------------")
                        docs.append(doc)
                    break  # Success, exit retry loop
                except Exception as e:
                    if attempt == max_retries - 1:  # Last attempt
                        if writer:
                            writer({"msg": f"Failed to scrape {url} after {max_retries} attempts: {str(e)}"})
                    else:
                        print("error", e)
                        time.sleep(1)  # Wait before retrying
                        continue
            
        except Exception as e:
            if writer:
                writer({"msg": f"Error scraping {url}: {str(e)}"})
            continue

    return {"scraped_content": docs}

def update_knowledge_base(state: State, writer: StreamWriter, config: Dict[str, Any]) -> AsyncIterator[Dict[str, Any]]:
    """Update the knowledge base with new information from search results"""
    writer({"msg": "Updating knowledge base..."})
    
    if not validate_state(state):
        writer({"msg": "Error: No question provided"})
        return {}
    
    llm = getModel("kb_model", config)
    parser = PydanticOutputParser(pydantic_object=KBUpdateResponse)
    
    try:
        # Get current knowledge base and search results
        current_kb = state.get("knowledge_base", [])
        search_results = state.get("search_results", [])
        
        if not search_results:
            writer({"msg": "No new search results to incorporate"})
            return {"knowledge_base": current_kb}
        
        # Get format instructions and create prompt
        format_instructions = parser.get_format_instructions()
        kb_update_prompt = create_kb_update_prompt(format_instructions)
        
        # Format the prompt with current KB and new search results
        current_date = datetime.now().strftime("%Y-%m-%d")
        formatted_prompt = kb_update_prompt.format(
            question=state["improved_question"],
            current_kb=json.dumps([nugget.dict() for nugget in current_kb]),
            search_results=json.dumps(search_results),
            current_date=current_date,
            format_instructions=format_instructions
        )
        
        # Get LLM's analysis of how to update the KB
        kb_update_response = llm.invoke(formatted_prompt)
        
        try:
            # Parse the response using Pydantic
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

def generate_answer(state: State, writer: StreamWriter, config: Dict[str, Any]) -> AsyncIterator[Dict[str, Any]]:
    """Generate an answer to the improved question in markdown format"""
    writer({"msg": "Generating answer ..."})
    
    if not validate_state(state):
        writer({"msg": "Error: No question provided"})
        return {}
    
    llm = getModel("answer_model", config)
    answer_prompt = create_direct_answer_prompt()
    
    try:
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
    writer({"msg": "Scoring answer against requirements..."})
    
    if not validate_state(state):
        writer({"msg": "Error: No question provided"})
        return {}
    
    llm = getModel("scoring_model", config)
    parser = PydanticOutputParser(pydantic_object=ChecklistResponse)
    
    try:
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

### Conditions
def should_continue_searching(state: State, config: Dict[str, Any], writer: StreamWriter) -> bool:
    """Check if we should continue searching based on checklist scores and max iterations"""
    writer({"msg": "Evaluating whether to continue searching..."})
    
    checklist = state.get("scored_checklist", [])
    if not checklist:
        writer({"msg": "No checklist available, stopping search"})
        return False
    
    # Get current iteration count from query history
    current_iterations = len(state.get("query_history", []))
    max_iterations = config["configurable"]["max_iterations"]
    
    # Check if we've reached max iterations
    if current_iterations >= max_iterations:
        writer({"msg": f"Reached maximum iterations ({max_iterations}), stopping search"})
        return False
    
    # Check if any item has a score less than the threshold
    score_threshold = config["configurable"]["score_threshold"]
    low_scores = [item for item in checklist if item.get("current_score", 0) < score_threshold]
    
    if low_scores:
        writer({"msg": f"Found {len(low_scores)} items below threshold ({score_threshold}), continuing search"})
        return True
    else:
        writer({"msg": "All items meet or exceed threshold, stopping search"})
        return False

### Graph

# Define the graph
graph_builder = StateGraph(State)

# Add nodes
graph_builder.add_node("improve_question", improve_question)
graph_builder.add_node("generate_scored_checklist", generate_scored_checklist)
graph_builder.add_node("generate_query", generate_query)
graph_builder.add_node("search2", search2)
graph_builder.add_node("get_best_urls_from_search", get_best_urls_from_search)
graph_builder.add_node("scrape_urls", scrape_urls)
graph_builder.add_node("update_knowledge_base", update_knowledge_base)
graph_builder.add_node("generate_answer", generate_answer)
graph_builder.add_node("score_answer", score_answer)

# Add edges
graph_builder.add_edge(START, "improve_question")
graph_builder.add_edge("improve_question", "generate_scored_checklist")
graph_builder.add_edge("generate_scored_checklist", "generate_query")
graph_builder.add_edge("generate_query", "search2")
graph_builder.add_edge("search2", "get_best_urls_from_search")
graph_builder.add_edge("get_best_urls_from_search", "scrape_urls")
graph_builder.add_edge("scrape_urls", "update_knowledge_base")
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