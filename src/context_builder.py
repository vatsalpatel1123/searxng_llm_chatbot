"""
Context Builder Module
Formats search results optimally for LLM consumption
"""

from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class ContextBuilder:
    """Builds optimized context from search results for LLM"""
    
    def __init__(self, config: Dict):
        """
        Initialize context builder
        
        Args:
            config: Configuration dictionary
        """
        self.context_config = config.get('context_building', {})
        self.max_tokens = self.context_config.get('max_context_tokens', 3000)
        self.format_style = self.context_config.get('format', 'structured')
        self.include_metadata = self.context_config.get('include_metadata', True)
        self.citation_format = self.context_config.get('citation_format', 
                                                       "[{index}] {title}\n    {snippet}\n    Source: {url}\n")
        
        logger.info("Context builder initialized")
    
    def build_context(self, results: List[Dict[str, Any]], 
                     query: str,
                     max_results: int = None) -> str:
        """
        Build formatted context from search results
        
        Args:
            results: List of search result dictionaries
            query: Original search query
            max_results: Maximum number of results to include
            
        Returns:
            Formatted context string
        """
        if not results:
            return "No search results available."
        
        # Limit results if specified
        if max_results:
            results = results[:max_results]
        
        if self.format_style == 'structured':
            context = self._build_structured_context(results, query)
        else:
            context = self._build_simple_context(results, query)
        
        # Ensure context doesn't exceed token limit
        context = self._truncate_to_token_limit(context)
        
        logger.debug(f"Built context with {len(results)} results (~{len(context)} chars)")
        
        return context
    
    def _build_structured_context(self, results: List[Dict], query: str) -> str:
        """
        Build structured, well-formatted context
        
        Args:
            results: Search results
            query: Original query
            
        Returns:
            Structured context
        """
        context_parts = []
        
        # Header
        context_parts.append("=" * 60)
        context_parts.append(f"SEARCH RESULTS FOR: {query}")
        context_parts.append("=" * 60)
        context_parts.append("")
        
        # Add each result
        for idx, result in enumerate(results, 1):
            title = result.get('title', 'Untitled')
            content = result.get('content', 'No description available.')
            url = result.get('url', '')
            engine = result.get('engine', 'unknown')
            
            # Format using template
            formatted_result = self.citation_format.format(
                index=idx,
                title=title,
                snippet=content,
                url=url
            )
            
            # Add metadata if enabled
            if self.include_metadata:
                formatted_result += f"    Engine: {engine}\n"
            
            context_parts.append(formatted_result)
        
        # Footer
        context_parts.append("")
        context_parts.append("=" * 60)
        context_parts.append(f"Total results: {len(results)}")
        context_parts.append("=" * 60)
        
        return "\n".join(context_parts)
    
    def _build_simple_context(self, results: List[Dict], query: str) -> str:
        """
        Build simple, compact context
        
        Args:
            results: Search results
            query: Original query
            
        Returns:
            Simple context
        """
        context_parts = [f"Search results for: {query}\n"]
        
        for idx, result in enumerate(results, 1):
            title = result.get('title', 'Untitled')
            content = result.get('content', 'No description.')
            url = result.get('url', '')
            
            context_parts.append(f"[{idx}] {title}")
            context_parts.append(f"    {content}")
            context_parts.append(f"    {url}\n")
        
        return "\n".join(context_parts)
    
    def _truncate_to_token_limit(self, context: str) -> str:
        """
        Truncate context to fit within token limit
        
        Args:
            context: Full context string
            
        Returns:
            Truncated context if needed
        """
        # Rough estimate: 4 chars per token
        estimated_tokens = len(context) // 4
        
        if estimated_tokens <= self.max_tokens:
            return context
        
        # Calculate how many characters to keep
        max_chars = self.max_tokens * 4
        
        logger.warning(f"Context truncated from ~{estimated_tokens} to ~{self.max_tokens} tokens")
        
        # Truncate with ellipsis
        truncated = context[:max_chars - 100]  # Leave room for message
        truncated += "\n\n[... Context truncated due to length ...]"
        
        return truncated
    
    def build_summary_context(self, results: List[Dict], query: str) -> str:
        """
        Build a brief summary context (for very long result sets)
        
        Args:
            results: Search results
            query: Original query
            
        Returns:
            Summary context
        """
        if not results:
            return "No results found."
        
        summary_parts = [
            f"Found {len(results)} results for: {query}",
            "",
            "Key findings:"
        ]
        
        # Include top 5 results with just titles and URLs
        for idx, result in enumerate(results[:5], 1):
            title = result.get('title', 'Untitled')
            url = result.get('url', '')
            summary_parts.append(f"[{idx}] {title} - {url}")
        
        if len(results) > 5:
            summary_parts.append(f"\n... and {len(results) - 5} more results")
        
        return "\n".join(summary_parts)
    
    def extract_key_info(self, results: List[Dict]) -> Dict[str, Any]:
        """
        Extract key information from results
        
        Args:
            results: Search results
            
        Returns:
            Dictionary with extracted info
        """
        # Count sources
        sources = set(result.get('url', '') for result in results)
        
        # Count engines
        engines = {}
        for result in results:
            engine = result.get('engine', 'unknown')
            engines[engine] = engines.get(engine, 0) + 1
        
        # Get top domains
        domains = {}
        for result in results:
            url = result.get('url', '')
            if url:
                try:
                    from urllib.parse import urlparse
                    domain = urlparse(url).netloc
                    domains[domain] = domains.get(domain, 0) + 1
                except:
                    pass
        
        return {
            'total_results': len(results),
            'unique_sources': len(sources),
            'engines': engines,
            'top_domains': dict(sorted(domains.items(), key=lambda x: x[1], reverse=True)[:5])
        }
    
    def format_citations(self, results: List[Dict]) -> str:
        """
        Format just the citations/sources list
        
        Args:
            results: Search results
            
        Returns:
            Formatted citations
        """
        citations = ["Sources:"]
        
        for idx, result in enumerate(results, 1):
            title = result.get('title', 'Untitled')
            url = result.get('url', '')
            citations.append(f"[{idx}] {title}")
            citations.append(f"     {url}")
        
        return "\n".join(citations)
