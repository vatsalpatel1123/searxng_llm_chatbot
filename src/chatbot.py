"""
Smart Chatbot Module
Main chatbot class integrating all components
"""

from typing import Dict, Any, Optional, List
import logging
import time
from pathlib import Path

from .config import Config, get_config
from .cache_manager import CacheManager, get_cache_manager
from .query_analyzer import QueryAnalyzer
from .searxng_client import SearXNGClient
from .llm_client import LLMClient
from .context_builder import ContextBuilder

logger = logging.getLogger(__name__)


class SmartChatbot:
    """
    Smart chatbot with integrated web search and LLM
    """
    
    def __init__(self, config_path: Optional[str] = None,
                 cache_enabled: bool = True,
                 verbose: bool = False):
        """
        Initialize smart chatbot
        
        Args:
            config_path: Path to config file (uses default if None)
            cache_enabled: Enable caching
            verbose: Enable verbose logging
        """
        # Setup logging
        self._setup_logging(verbose)
        
        logger.info("Initializing Smart Chatbot...")
        
        # Load configuration
        self.config = get_config(config_path)
        
        # Initialize components
        self.query_analyzer = QueryAnalyzer(self.config._config)
        self.searxng = SearXNGClient(self.config._config)
        self.llm = LLMClient(self.config._config)
        self.context_builder = ContextBuilder(self.config._config)
        
        # Initialize cache if enabled
        self.cache_enabled = cache_enabled and self.config.cache_enabled
        if self.cache_enabled:
            self.cache = get_cache_manager(
                cache_dir=str(self.config.cache_directory),
                default_ttl=self.config.get('cache.ttl.general', 86400),
                max_entries=self.config.get('cache.max_entries', 1000)
            )
            
            # Cleanup expired cache on start
            if self.config.get('cache.cleanup_on_start', True):
                self.cache.cleanup_expired()
        
        # Test connections
        self._test_connections()
        
        logger.info("Smart Chatbot initialized successfully!")
    
    def _setup_logging(self, verbose: bool):
        """Setup logging configuration"""
        level = logging.DEBUG if verbose else logging.INFO
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(formatter)
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(level)
        root_logger.addHandler(console_handler)
    
    def _test_connections(self):
        """Test connections to SearXNG and LLM"""
        logger.info("Testing connections...")
        
        # Test SearXNG
        try:
            if self.searxng.test_connection():
                logger.info("✓ SearXNG connection OK")
            else:
                logger.warning("✗ SearXNG connection failed (will continue anyway)")
        except Exception as e:
            logger.warning(f"✗ SearXNG connection error: {e}")
        
        # Test LLM
        try:
            if self.llm.test_connection():
                logger.info("✓ LLM connection OK")
            else:
                logger.warning("✗ LLM connection failed (will continue anyway)")
        except Exception as e:
            logger.warning(f"✗ LLM connection error: {e}")
    
    def chat(self, query: str, 
             force_search: bool = False,
             skip_cache: bool = False,
             max_results: int = None) -> Dict[str, Any]:
        """
        Main chat method with intelligent search integration
        
        Args:
            query: User query
            force_search: Force web search even if not needed
            skip_cache: Skip cache lookup
            max_results: Maximum search results to use
            
        Returns:
            Dictionary with answer, sources, and metadata
        """
        start_time = time.time()
        
        logger.info(f"Processing query: {query}")
        
        # Analyze query
        analysis = self.query_analyzer.analyze(query)
        needs_search = analysis['needs_search'] or force_search
        
        logger.info(f"Search decision: {needs_search} (reason: {analysis['reason']})")
        
        response = {
            'query': query,
            'answer': '',
            'sources': [],
            'search_used': needs_search,
            'cached': False,
            'analysis': analysis,
            'response_time': 0
        }
        
        try:
            if needs_search:
                # Attempt search-based response
                result = self._search_and_answer(
                    query, 
                    analysis,
                    skip_cache,
                    max_results
                )
                response.update(result)
            else:
                # Direct LLM response
                answer = self.llm.chat_simple(query)
                response['answer'] = answer
                response['search_used'] = False
        
        except Exception as e:
            logger.error(f"Error processing query: {e}", exc_info=True)
            response['answer'] = f"I encountered an error: {str(e)}"
            response['error'] = str(e)
        
        response['response_time'] = time.time() - start_time
        logger.info(f"Query processed in {response['response_time']:.2f}s")
        
        return response
    
    def _search_and_answer(self, query: str, 
                           analysis: Dict,
                           skip_cache: bool,
                           max_results: Optional[int]) -> Dict[str, Any]:
        """
        Perform search and generate answer
        
        Args:
            query: User query
            analysis: Query analysis results
            skip_cache: Skip cache
            max_results: Max results
            
        Returns:
            Response dictionary
        """
        # Check cache first
        if self.cache_enabled and not skip_cache:
            cached_response = self.cache.get(query)
            if cached_response:
                logger.info("Using cached response")
                return {
                    'answer': cached_response['answer'],
                    'sources': cached_response['sources'],
                    'cached': True
                }
        
        # Perform search
        category = analysis.get('search_category', 'general')
        
        logger.info(f"Searching SearXNG (category: {category})...")
        search_results = self.searxng.search(
            query, 
            category=category,
            num_results=max_results
        )
        
        if not search_results:
            logger.warning("No search results found, falling back to LLM knowledge")
            answer = self.llm.chat_simple(
                f"{query}\n\nNote: No current web results available. " +
                "Please provide an answer based on your knowledge."
            )
            return {
                'answer': answer,
                'sources': [],
                'cached': False
            }
        
        # Build context from results
        logger.info(f"Building context from {len(search_results)} results...")
        context = self.context_builder.build_context(
            search_results,
            query,
            max_results=max_results
        )
        
        # Generate answer with context
        logger.info("Generating answer with LLM...")
        answer = self.llm.chat_with_context(query, context)
        
        # Extract sources
        sources = [
            {
                'title': r['title'],
                'url': r['url'],
                'snippet': r['content'][:200]
            }
            for r in search_results[:5]  # Top 5 sources
        ]
        
        result = {
            'answer': answer,
            'sources': sources,
            'cached': False
        }
        
        # Cache the response
        if self.cache_enabled:
            ttl = self.cache.get_cache_ttl_for_query(query)
            self.cache.set(query, result, ttl=ttl)
            logger.debug(f"Cached response (TTL: {ttl}s)")
        
        return result
    
    def chat_simple(self, query: str) -> str:
        """
        Simple chat method returning just the answer
        
        Args:
            query: User query
            
        Returns:
            Answer string
        """
        response = self.chat(query)
        return response['answer']
    
    def get_sources(self, query: str) -> List[Dict]:
        """
        Get just the sources for a query
        
        Args:
            query: Search query
            
        Returns:
            List of source dictionaries
        """
        analysis = self.query_analyzer.analyze(query)
        category = analysis.get('search_category', 'general')
        
        results = self.searxng.search(query, category=category)
        
        return [
            {
                'title': r['title'],
                'url': r['url'],
                'snippet': r['content']
            }
            for r in results
        ]
    
    def clear_cache(self):
        """Clear all cached responses"""
        if self.cache_enabled:
            self.cache.clear()
            logger.info("Cache cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get chatbot statistics
        
        Returns:
            Statistics dictionary
        """
        stats = {
            'config_loaded': True,
            'cache_enabled': self.cache_enabled,
        }
        
        if self.cache_enabled:
            stats['cache_stats'] = self.cache.get_stats()
        
        return stats
    
    def __repr__(self) -> str:
        return f"SmartChatbot(cache_enabled={self.cache_enabled})"
