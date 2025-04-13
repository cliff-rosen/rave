# LangChain and LangGraph Experimental Project

This project demonstrates the use of LangChain and LangGraph to create a simple conversational agent with memory and state management.

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the project root and add your OpenAI API key:
```
OPENAI_API_KEY=your_api_key_here
```

## Project Structure

- `src/`: Contains the main source code
  - `agents/`: Agent implementations
  - `chains/`: Chain implementations
  - `graphs/`: LangGraph implementations
- `examples/`: Example scripts demonstrating different features

## Features

- Basic conversational agent with memory
- State management using LangGraph
- Custom chain implementations
- Graph-based workflow orchestration 