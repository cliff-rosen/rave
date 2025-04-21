import os
import streamlit as st

# API Keys and Authentication
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
TAVILY_API_KEY = st.secrets["TAVILY_API_KEY"]
SERPAPI_API_KEY = st.secrets["SERPAPI_API_KEY"]

# Agent Configuration
MAX_ITERATIONS = 3
SCORE_THRESHOLD = 0.9
IMPROVEMENT_THRESHOLD = 0.05

# Model Configuration
DEFAULT_MODEL = "gpt-4o-mini"
FALLBACK_MODEL = "gpt-3.5-turbo"

# Search Configuration
MAX_SEARCH_RESULTS = 3
SEARCH_TIMEOUT = 30  # seconds

# Logging Configuration
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Error messages
ERROR_MESSAGES = {
    "api_error": "An error occurred while communicating with the API.",
    "validation_error": "The input data is invalid.",
    "search_error": "An error occurred during the search operation.",
    "timeout_error": "The operation timed out.",
} 