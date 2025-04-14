from langchain_core.prompts import ChatPromptTemplate

def create_evaluator_prompt():
    return ChatPromptTemplate.from_messages([
        ("system", "You are an evaluator that assesses responses against a scorecard. Return a JSON object with 'score' and 'feedback' fields."),
        ("user", """Evaluate the following response against the scorecard criteria:
        Response: {current_attempt}
        Scorecard Criteria:
        - Completeness: How well does it cover all aspects of the topic?
        - Accuracy: How accurate are the facts presented?
        - Relevance: How well does it address the specific question?
        - Clarity: How clear and well-structured is the explanation?
        
        Return a JSON object with:
        {{
            "score": {{
                "completeness": <float 0-1>,
                "accuracy": <float 0-1>,
                "relevance": <float 0-1>,
                "clarity": <float 0-1>
            }},
            "feedback": <string describing what needs improvement>
        }}

        Example response:
        {{
            "score": {{
                "completeness": 0.8,
                "accuracy": 0.9,
                "relevance": 0.85,
                "clarity": 0.75
            }},
            "feedback": "The response covers the main points but could be more detailed in explaining the differences between supervised and unsupervised learning."
        }}""")
    ])

def create_gap_analyzer_prompt():
    return ChatPromptTemplate.from_messages([
        ("system", "You analyze gaps in responses based on evaluation feedback."),
        ("user", """Analyze the following response and feedback to identify specific gaps:
        Response: {response}
        Feedback: {feedback}
        List the specific deficiencies or missing elements.""")
    ])

def create_query_generator_prompt():
    return ChatPromptTemplate.from_messages([
        ("system", "You generate targeted search queries based on identified gaps. Return only the search queries, one per line."),
        ("user", """Generate search queries to address these gaps:
        Gaps: {gaps}
        Original Query: {query}
        Previous Queries: {search_history}
        
        Generate only the search queries, one per line. Do not include any explanations or examples.""")
    ])
                                     
def create_response_generator_prompt():
    return ChatPromptTemplate.from_messages([
        ("system", "You generate improved responses by incorporating new information. Focus on addressing the specific gaps identified in the previous evaluation."),
        ("user", """Generate an improved response incorporating the new information:
        Original Query: {query}
        
        New Information:
        {new_info}
        
        Previous Attempt:
        {previous_attempt}
        
        Generate a comprehensive response that addresses any gaps in the previous attempt while maintaining its strengths.""")
    ])

def create_direct_answer_prompt():
    """Simple prompt that directly answers the question without any additional processing"""
    return ChatPromptTemplate.from_messages([
        ("system", "You are a helpful assistant that provides direct answers to questions."),
        ("user", "{question}")
    ]) 