from typing import Optional
from pydantic import SecretStr
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI

# LLM model mappings
LLM_MODELS = {
    "OpenAI": ["gpt-4o", "o3-mini"],
    "Anthropic": ["claude-3-5-sonnet-20240620", "claude-3-7-sonnet-20250219"],
    "Google": ["gemini-1.5-flash-002", "gemini-2.0-flash-exp"],
    "alibaba": ["qwen-2.5-72b-instruct"]
}

def get_llm(provider: str, model: str, api_key: str) -> Optional[object]:
    """Initialize LLM based on provider"""
    try:
        if provider == "OpenAI":
            return ChatOpenAI(model=model, api_key=SecretStr(api_key))
        elif provider == "Anthropic":
            return ChatAnthropic(model=model, api_key=SecretStr(api_key))
        elif provider == "Google":
            return ChatGoogleGenerativeAI(model=model, api_key=SecretStr(api_key))
        else:
            raise ValueError(f"Unsupported provider: {provider}")
    except Exception as e:
        raise ValueError(f"Failed to initialize {provider} LLM: {str(e)}") 