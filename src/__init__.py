"""
SearXNG LLM Chatbot
Smart chatbot with integrated web search and local LLM
"""

from .chatbot import SmartChatbot
from .config import Config, get_config
from .cache_manager import CacheManager
from .query_analyzer import QueryAnalyzer
from .searxng_client import SearXNGClient
from .llm_client import LLMClient
from .context_builder import ContextBuilder

__version__ = '1.0.0'
__all__ = [
    'SmartChatbot',
    'Config',
    'get_config',
    'CacheManager',
    'QueryAnalyzer',
    'SearXNGClient',
    'LLMClient',
    'ContextBuilder'
]
