from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from typing import List, Optional
import random
from datetime import datetime

class ChecklistItem(BaseModel):
    item_to_score: str = Field(description="A specific requirement that should be addressed in the answer")
    current_score: float = Field(description="Score between 0 and 1", ge=0, le=1, default=0.0)

class ChecklistResponse(BaseModel):
    items: List[ChecklistItem] = Field(description="List of requirements for a complete answer")

class KnowledgeNugget(BaseModel):
    """A piece of information with its source"""
    content: str = Field(description="The actual information content")
    source_url: str = Field(description="URL where this information was found")
    confidence: float = Field(description="Confidence in this information (0-1)", ge=0, le=1, default=1.0)
    conflicts_with: List[str] = Field(description="List of nugget IDs this conflicts with", default_factory=list)
    nugget_id: str = Field(description="Unique identifier for this nugget", default_factory=lambda: str(random.randint(1000, 9999)))

class KnowledgeNuggetUpdate(BaseModel):
    """Update to an existing knowledge nugget"""
    nugget_id: str
    content: Optional[str] = None
    confidence: Optional[float] = None
    conflicts_with: Optional[List[str]] = None

class KBUpdateResponse(BaseModel):
    """Response format for knowledge base updates"""
    new_nuggets: List[KnowledgeNugget] = Field(default_factory=list)
    updated_nuggets: List[KnowledgeNuggetUpdate] = Field(default_factory=list)

class URLWithScore(BaseModel):
    """A URL with its relevance score"""
    url: str = Field(description="The URL to scrape")
    score: int = Field(description="Relevance score from 0 to 100", ge=0, le=100)

class URLSelectionResponse(BaseModel):
    """Response format for URL selection"""
    urls: List[URLWithScore] = Field(description="List of URLs to scrape with their relevance scores")

def create_evaluator_prompt():
    """Create a prompt for evaluating answers"""
    return ChatPromptTemplate.from_messages([
        ("system", """You are an expert at evaluating answers for completeness and accuracy.
        Analyze the answer and identify any gaps or areas that need improvement."""),
        ("user", "{answer}")
    ])

def create_gap_analyzer_prompt():
    """Create a prompt for analyzing gaps in answers"""
    return ChatPromptTemplate.from_messages([
        ("system", """You are an expert at identifying knowledge gaps in answers.
        Analyze the answer and identify specific areas where more information is needed."""),
        ("user", "{answer}")
    ])

def create_query_generator_prompt():
    """Create a prompt for generating search queries"""
    current_date = datetime.now().strftime("%Y-%m-%d")
    return ChatPromptTemplate.from_messages([
        ("system", f"""You are an expert at generating effective search queries.
        Based on the question and checklist requirements, generate a search query that will help find relevant information.
        Consider the query history to avoid repeating similar searches.
        The query should be specific and focused on finding information that will help address the checklist requirements.
        Current date: {current_date}
        
        Return only the search query text, nothing else."""),
        ("user", """Question: {question}
        Checklist Requirements: {checklist}
        Previous Queries: {query_history}
        
        Generate a new search query:""")
    ])

def create_response_generator_prompt():
    """Create a prompt for generating improved responses"""
    return ChatPromptTemplate.from_messages([
        ("system", """You are an expert at generating clear and comprehensive answers.
        Use the search results to improve the answer and fill in the gaps."""),
        ("user", """Original answer: {answer}
        Search results: {search_results}
        Gaps to address: {gaps}""")
    ])

def create_direct_answer_prompt():
    """Create a prompt for generating direct answers"""
    current_date = datetime.now().strftime("%Y-%m-%d")
    return ChatPromptTemplate.from_messages([
        ("system", f"""You are an expert at providing clear and comprehensive answers.
        Your task is to generate an answer that addresses all the requirements in the checklist.
        Use the knowledge base to enhance your answer with relevant information.
        Make sure to cite sources when using information from the knowledge base.
        Current date: {current_date}
        
        For each requirement in the checklist:
        1. Ensure your answer directly addresses it
        2. Provide specific details and examples where relevant
        3. Use knowledge base information to support your points
        4. If a requirement isn't fully addressed, acknowledge the gap
        5. When citing information, include the source URL
        6. For conflicting information, acknowledge the conflict and explain the different perspectives
        
        Structure your answer to be clear, well-organized, and comprehensive."""),
        ("user", """Question: {question}
        Checklist Requirements: {checklist}
        Knowledge Base: {knowledge_base}
        
        Generate a comprehensive answer that addresses all checklist requirements:""")
    ])

def create_question_improvement_prompt():
    """Create a prompt for improving questions"""
    return ChatPromptTemplate.from_messages([
        ("system", """You are an expert at improving questions for clarity and completeness.
        Make the question more specific and clear while preserving its intent."""),
        ("user", "{question}")
    ])

def create_checklist_prompt(format_instructions: str):
    """Create a prompt for generating answer requirements checklist"""
    return ChatPromptTemplate.from_messages([
        ("system", """You are an expert at breaking down questions into specific requirements for a complete answer.
        For the given question, generate a list of specific items that should be addressed in a well-formed answer.
        Each item should be a clear, specific requirement that can be scored independently.
        {format_instructions}"""),
        ("user", "{question}")
    ])

def create_scoring_prompt(format_instructions: str):
    """Create a prompt for scoring answers against checklist requirements"""
    return ChatPromptTemplate.from_messages([
        ("system", """You are an expert at evaluating answers against specific requirements.
        For each requirement in the checklist, score how well the answer addresses it on a scale of 0 to 1.
        {format_instructions}"""),
        ("user", """Question: {question}
        Answer: {answer}
        Checklist: {checklist}
        
        Score each item in the checklist and return the updated checklist with scores.""")
    ])

def create_kb_update_prompt(format_instructions: str):
    """Create a prompt for updating the knowledge base with new information"""
    return ChatPromptTemplate.from_messages([
        ("system", """You are an expert at analyzing and integrating information.
        Your task is to update the knowledge base with new information from search results.
        Current date: {current_date}
        
        For each piece of information:
        1. Compare it with existing knowledge
        2. Identify any conflicts or corroborations
        3. Update confidence scores based on multiple sources
        4. Create new nuggets for unique information
        5. Update existing nuggets when new information is found
        
        When conflicts are found:
        1. Create a new nugget documenting the conflict
        2. Link conflicting nuggets together
        3. Adjust confidence scores based on source reliability
        
        You MUST return a JSON object following these format instructions exactly:
        {format_instructions}"""),
        ("user", """Question: {question}
        Current Knowledge Base: {current_kb}
        New Search Results: {search_results}
        
        Analyze and update the knowledge base. Return a JSON object following the format instructions exactly:""")
    ])

def create_url_selection_prompt(format_instructions: str):
    """Create a prompt for selecting the most relevant URLs from search results"""
    return ChatPromptTemplate.from_messages([
        ("system", """You are an expert at analyzing search results and identifying the most relevant sources.
        Your task is to select the URLs that are most likely to contain information that will help answer the question.
        
        For each search result:
        1. Analyze the title and snippet to determine relevance
        2. Consider the source's credibility and authority
        3. Prioritize sources that appear to directly address the question
        4. Select a diverse set of sources to ensure comprehensive coverage
        5. Assign a relevance score from 0 to 100 for each URL based on:
           - How directly it addresses the question
           - Source credibility and authority
           - Content depth and comprehensiveness
           - Recency and timeliness
        
        {format_instructions}"""),
        ("user", """Question: {question}
        Search Results: {search_results}
        
        Select the most relevant URLs to scrape and assign each a relevance score:""")
    ]) 