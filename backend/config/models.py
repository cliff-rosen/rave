from enum import Enum
from typing import Dict, Any

class OpenAIModel(Enum):
    """Enumeration of OpenAI models with their specifications"""
    
    # O-Series Reasoning Models
    O3_MINI = {
        "name": "o3-mini",
        "context_window": 128000,
        "use_cases": [
            "Fast, flexible reasoning",
            "Multi-step tasks",
            "Complex problem solving"
        ],
        "cost_per_1k_tokens": 0.01,  # Input
        "supports_temperature": False
    }
    
    O1 = {
        "name": "o1",
        "context_window": 128000,
        "use_cases": [
            "High-intelligence reasoning",
            "Complex analysis",
            "Advanced problem solving"
        ],
        "cost_per_1k_tokens": 0.02,  # Input
        "supports_temperature": False
    }
    
    O1_MINI = {
        "name": "o1-mini",
        "context_window": 128000,
        "use_cases": [
            "Fast reasoning",
            "Cost-effective analysis",
            "Quick problem solving"
        ],
        "cost_per_1k_tokens": 0.015,  # Input
        "supports_temperature": False
    }
    
    O1_PRO = {
        "name": "o1-pro",
        "context_window": 128000,
        "use_cases": [
            "Advanced reasoning",
            "High-precision analysis",
            "Complex multi-step tasks"
        ],
        "cost_per_1k_tokens": 0.03,  # Input
        "supports_temperature": False
    }
    
    # Flagship Chat Models
    GPT41 = {
        "name": "gpt-4.1",
        "context_window": 128000,
        "use_cases": [
            "Complex tasks",
            "Advanced reasoning",
            "High-precision responses"
        ],
        "cost_per_1k_tokens": 0.03,  # Input
        "supports_temperature": True
    }
    
    GPT4O = {
        "name": "gpt-4o",
        "context_window": 128000,
        "use_cases": [
            "Fast, intelligent responses",
            "Flexible task handling",
            "General purpose chat"
        ],
        "cost_per_1k_tokens": 0.02,  # Input
        "supports_temperature": True
    }
    
    GPT4O_AUDIO = {
        "name": "gpt-4o-audio-preview",
        "context_window": 128000,
        "use_cases": [
            "Audio input/output",
            "Voice interactions",
            "Audio processing"
        ],
        "cost_per_1k_tokens": 0.02,  # Input
        "supports_temperature": True
    }
    
    CHATGPT4O = {
        "name": "chatgpt-4o-latest",
        "context_window": 128000,
        "use_cases": [
            "ChatGPT-like interactions",
            "Conversational AI",
            "General purpose chat"
        ],
        "cost_per_1k_tokens": 0.02,  # Input
        "supports_temperature": True
    }
    
    # Cost-Optimized Models
    GPT41_MINI = {
        "name": "gpt-4.1-mini",
        "context_window": 128000,
        "use_cases": [
            "Balanced intelligence and speed",
            "Cost-effective tasks",
            "General purpose chat"
        ],
        "cost_per_1k_tokens": 0.015,  # Input
        "supports_temperature": True
    }
    
    GPT41_NANO = {
        "name": "gpt-4.1-nano",
        "context_window": 128000,
        "use_cases": [
            "Fastest responses",
            "Most cost-effective",
            "Simple tasks"
        ],
        "cost_per_1k_tokens": 0.01,  # Input
        "supports_temperature": True
    }
    
    GPT4O_MINI = {
        "name": "gpt-4o-mini",
        "context_window": 128000,
        "use_cases": [
            "Focused tasks",
            "Fast responses",
            "Cost-effective chat"
        ],
        "cost_per_1k_tokens": 0.01,  # Input
        "supports_temperature": True
    }
    
    GPT4O_MINI_AUDIO = {
        "name": "gpt-4o-mini-audio-preview",
        "context_window": 128000,
        "use_cases": [
            "Audio input/output",
            "Voice interactions",
            "Cost-effective audio processing"
        ],
        "cost_per_1k_tokens": 0.01,  # Input
        "supports_temperature": True
    }
    
    # Legacy Models
    GPT4_TURBO = {
        "name": "gpt-4-turbo-preview",
        "context_window": 128000,
        "use_cases": [
            "Complex reasoning",
            "Answer generation",
            "Question improvement",
            "Knowledge verification"
        ],
        "cost_per_1k_tokens": 0.01,  # Input
        "supports_temperature": True
    }
    
    GPT4 = {
        "name": "gpt-4",
        "context_window": 8192,
        "use_cases": [
            "Answer generation",
            "Question improvement",
            "Knowledge verification"
        ],
        "cost_per_1k_tokens": 0.03,  # Input
        "supports_temperature": True
    }
    
    GPT4_32K = {
        "name": "gpt-4-32k",
        "context_window": 32768,
        "use_cases": [
            "Long-form content analysis",
            "Large document processing",
            "Complex multi-step reasoning"
        ],
        "cost_per_1k_tokens": 0.06,  # Input
        "supports_temperature": True
    }
    
    # GPT-3.5 Models
    GPT35_TURBO = {
        "name": "gpt-3.5-turbo",
        "context_window": 16384,
        "use_cases": [
            "Query generation",
            "Initial question processing",
            "Simple reasoning tasks"
        ],
        "cost_per_1k_tokens": 0.001,  # Input
        "supports_temperature": True
    }
    
    GPT35_TURBO_INSTRUCT = {
        "name": "gpt-3.5-turbo-instruct",
        "context_window": 4096,
        "use_cases": [
            "Structured tasks",
            "Checklist generation",
            "Precise instruction following"
        ],
        "cost_per_1k_tokens": 0.0015,  # Input
        "supports_temperature": True
    }
    
    # Embedding Models
    EMBEDDING_3_SMALL = {
        "name": "text-embedding-3-small",
        "context_window": 8191,
        "use_cases": [
            "Knowledge base management",
            "Semantic search",
            "Document comparison"
        ],
        "cost_per_1k_tokens": 0.00002,
        "supports_temperature": False
    }
    
    EMBEDDING_3_LARGE = {
        "name": "text-embedding-3-large",
        "context_window": 8191,
        "use_cases": [
            "High-precision embeddings",
            "Advanced semantic search",
            "Complex document analysis"
        ],
        "cost_per_1k_tokens": 0.00013,
        "supports_temperature": False
    }

# Default model configurations
DEFAULT_MODEL = OpenAIModel.GPT4O.value["name"]  # Using the latest GPT-4o model
DEFAULT_EMBEDDING_MODEL = OpenAIModel.EMBEDDING_3_SMALL.value["name"]

def get_model_config(model_name: str) -> Dict[str, Any]:
    """Get the configuration for a specific model by name"""
    for model in OpenAIModel:
        if model.value["name"] == model_name:
            return model.value
    raise ValueError(f"Model {model_name} not found in configuration") 