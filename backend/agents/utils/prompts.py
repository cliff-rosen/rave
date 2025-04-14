from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from typing import List

class ChecklistItem(BaseModel):
    item_to_score: str = Field(description="A specific requirement that should be addressed in the answer")
    current_score: float = Field(description="Score between 0 and 1", ge=0, le=1, default=0.0)

class ChecklistResponse(BaseModel):
    items: List[ChecklistItem] = Field(description="List of requirements for a complete answer")

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
    return ChatPromptTemplate.from_messages([
        ("system", """You are an expert at generating effective search queries.
        Create a search query that will help find information to fill the identified gaps."""),
        ("user", "{gaps}")
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
    return ChatPromptTemplate.from_messages([
        ("system", """You are an expert at providing clear and comprehensive answers.
        Answer the question directly and thoroughly."""),
        ("user", "{question}")
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