import sys
import os
from datetime import datetime

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from backend.agents.utils.prompts import create_kb_update_prompt
from backend.agents.utils.prompts import KBUpdateResponse
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate

def main():
    # Get format instructions
    parser = PydanticOutputParser(pydantic_object=KBUpdateResponse)
    format_instructions = parser.get_format_instructions()
    
    # Create the prompt using the actual function
    prompt = create_kb_update_prompt(format_instructions)
    
    # Try to format the prompt
    try:
        current_date = datetime.now().strftime("%Y-%m-%d")
        formatted_prompt = prompt.format(
            question="test question",
            current_kb="[]",
            search_results="[]",
            current_date=current_date,
            format_instructions=format_instructions
        )
        print("Formatted prompt successfully:")
        print(formatted_prompt)
    except Exception as e:
        print(f"Error formatting prompt: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 