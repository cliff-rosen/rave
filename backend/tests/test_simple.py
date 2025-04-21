import sys
from pathlib import Path

# Add project root to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

from backend.agents.rave_agent import search2

res = search2(
    {"question": "What is the capital of France?",
     "current_query": "What is the capital of France?"}, 
     writer=None)

print(res)

