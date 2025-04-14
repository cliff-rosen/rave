# RAVE - Recursive Agent for Verified Explanations

RAVE is an advanced AI agent system that uses a recursive approach to generate, verify, and improve responses to user queries. It combines the power of large language models with structured verification and improvement processes to deliver high-quality, accurate information.

## Features

- 🤖 Recursive improvement of responses
- ✅ Built-in verification and fact-checking
- 🔍 Automated gap analysis and improvement
- 📊 Response quality scoring
- 💻 Modern Streamlit interface
- 🔄 Conversation history tracking

## Project Structure

```
rave/
├── frontend/           # Streamlit web interface
│   ├── app.py         # Main Streamlit application
│   ├── pages/         # Additional Streamlit pages
│   ├── components/    # Reusable UI components
│   └── static/        # Static assets (CSS, images)
├── backend/           # Backend implementation
│   ├── agents/        # Agent implementation
│   ├── config/        # Configuration files
│   └── api/           # API endpoints
├── tests/             # Test suite
├── docs/              # Documentation
└── requirements.txt   # Project dependencies
```

## Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/rave.git
   cd rave
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   Create a `.env` file in the root directory with:
   ```
   OPENAI_API_KEY=your_openai_api_key
   TAVILY_API_KEY=your_tavily_api_key
   ```

5. Run the application:
   ```bash
   streamlit run frontend/app.py
   ```

## Usage

1. Start the application using the command above
2. Enter your query in the text input field
3. Watch as RAVE processes your query through multiple iterations
4. Review the final response and its quality metrics
5. Access previous conversations through the history panel

## Development

- Use `black` for code formatting
- Use `isort` for import sorting
- Use `flake8` for linting
- Run tests with `pytest`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 