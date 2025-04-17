from langchain_core.prompts import ChatPromptTemplate

def main():
    # Create a simple prompt template
    format_instructions = "These are the format instructions"
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Test system message with {format_instructions}"),
        ("user", "Test user message")
    ]).partial(format_instructions=format_instructions)
    
    # Now format with the remaining variables
    try:
        formatted_prompt = prompt.format(
            question="test question",
            current_kb="[]",
            search_results="[]"
        )
        print("Success!")
        print(formatted_prompt)
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main() 