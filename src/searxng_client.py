"""
SearXNG Client Module
Optimized client for interacting with SearXNG search engine
"""

import requests
from typing import List, Dict, Optional, Any
from urllib.parse import urljoin, quote
import logging
from bs4 import BeautifulSoup
import validators

logger = logging.getLogger(__name__)


class SearXNGClient:
    """Client for SearXNG search engine with result optimization"""
    
    def __init__(self, config: Dict):
        """
        Initialize SearXNG client
        
        Args:
            config: Configuration dictionary
        """
        self.base_url = config.get('searxng', {}).get('url', 'http://localhost:8080')
        self.timeout = config.get('searxng', {}).get('timeout', 15)
        self.max_results = config.get('searxng', {}).get('max_results', 10)
        
        self.enabled_engines = config.get('searxng', {}).get('enabled_engines', [])
        self.disabled_engines = config.get('searxng', {}).get('disabled_engines', [])
        
        self.result_config = config.get('result_processing', {})
        self.min_results = self.result_config.get('min_results', 2)
        self.blacklist_domains = set(self.result_config.get('blacklist_domains', []))
        self.whitelist_domains = set(self.result_config.get('whitelist_domains', []))
        self.max_snippet_length = self.result_config.get('max_snippet_length', 300)
        
        # Scoring weights
        self.scoring = self.result_config.get('scoring', {})
        
        logger.info(f"SearXNG client initialized (URL: {self.base_url})")
    
    def search(self, query: str, category: str = 'general', 
               num_results: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Perform search using SearXNG
        
        Args:
            query: Search query
            category: Search category (general, news, academic, etc.)
            num_results: Number of results to return
            
        Returns:
            List of search result dictionaries
        """
        if num_results is None:
            num_results = self.max_results
        
        logger.info(f"Searching for: '{query}' (category: {category})")
        
        try:
            # Make search request
            results = self._make_request(query, category)
            
            if not results:
                logger.warning(f"No results found for query: {query}")
                return []
            
            # Filter and process results
            filtered_results = self._filter_results(results)
            
            # Rank results
            ranked_results = self._rank_results(filtered_results, query)
            
            # Limit results
            final_results = ranked_results[:num_results]
            
            logger.info(f"Returning {len(final_results)} results for query: {query}")
            
            return final_results
            
        except Exception as e:
            logger.error(f"Search error: {e}", exc_info=True)
            return []
    
    def _make_request(self, query: str, category: str) -> List[Dict]:
        """
        Make HTTP request to SearXNG
        
        Args:
            query: Search query
            category: Search category
            
        Returns:
            Raw search results
        """
        search_url = urljoin(self.base_url, '/search')
        
        params = {
            'q': query,
            'format': 'json',
            'categories': category,
            'language': 'en'
        }
        
        # Add disabled engines if configured
        if self.disabled_engines:
            params['disabled_engines'] = ','.join(self.disabled_engines)
        
        try:
            response = requests.get(
                search_url,
                params=params,
                timeout=self.timeout,
                headers={'User-Agent': 'SmartChatbot/1.0'}
            )
            
            response.raise_for_status()
            data = response.json()
            
            results = data.get('results', [])
            logger.debug(f"Received {len(results)} raw results from SearXNG")
            
            return results
            
        except requests.exceptions.Timeout:
            logger.error(f"SearXNG request timeout after {self.timeout}s")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"SearXNG request error: {e}")
            raise
        except ValueError as e:
            logger.error(f"Invalid JSON response: {e}")
            raise
    
    def _filter_results(self, results: List[Dict]) -> List[Dict]:
        """
        Filter and clean search results
        
        Args:
            results: Raw search results
            
        Returns:
            Filtered results
        """
        filtered = []
        seen_urls = set()
        
        for result in results:
            # Extract fields
            url = result.get('url', '')
            title = result.get('title', '')
            content = result.get('content', '')
            
            # Skip if missing essential fields
            if not url or not title:
                continue
            
            # Validate URL
            if not validators.url(url):
                logger.debug(f"Invalid URL: {url}")
                continue
            
            # Check for blacklisted domains
            if self._is_blacklisted(url):
                logger.debug(f"Blacklisted domain: {url}")
                continue
            
            # Remove duplicates
            if url in seen_urls:
                logger.debug(f"Duplicate URL: {url}")
                continue
            
            seen_urls.add(url)
            
            # Clean and truncate content
            clean_content = self._clean_text(content)
            if len(clean_content) > self.max_snippet_length:
                clean_content = clean_content[:self.max_snippet_length] + '...'
            
            # Build clean result
            clean_result = {
                'title': self._clean_text(title),
                'url': url,
                'content': clean_content,
                'engine': result.get('engine', 'unknown'),
                'score': result.get('score', 0),
                'category': result.get('category', 'general')
            }
            
            filtered.append(clean_result)
        
        logger.debug(f"Filtered to {len(filtered)} results")
        return filtered
    
    def _is_blacklisted(self, url: str) -> bool:
        """
        Check if URL domain is blacklisted
        
        Args:
            url: URL to check
            
        Returns:
            True if blacklisted
        """
        for domain in self.blacklist_domains:
            if domain in url:
                return True
        return False
    
    def _clean_text(self, text: str) -> str:
        """
        Clean and normalize text
        
        Args:
            text: Raw text
            
        Returns:
            Cleaned text
        """
        if not text:
            return ''
        
        # Remove HTML tags if any
        soup = BeautifulSoup(text, 'html.parser')
        text = soup.get_text()
        
        # Normalize whitespace
        text = ' '.join(text.split())
        
        return text.strip()
    
    def _rank_results(self, results: List[Dict], query: str) -> List[Dict]:
        """
        Rank results by relevance
        
        Args:
            results: Search results
            query: Original query
            
        Returns:
            Ranked results
        """
        query_lower = query.lower()
        query_terms = set(query_lower.split())
        
        for result in results:
            score = 0.0
            
            title = result.get('title', '').lower()
            content = result.get('content', '').lower()
            url = result.get('url', '').lower()
            
            # Title match score
            title_terms = set(title.split())
            title_matches = len(query_terms & title_terms)
            score += title_matches * self.scoring.get('title_match', 3.0)
            
            # Content match score
            content_terms = set(content.split())
            content_matches = len(query_terms & content_terms)
            score += content_matches * self.scoring.get('content_match', 2.0)
            
            # Exact phrase match bonus
            if query_lower in title:
                score += 5.0
            elif query_lower in content:
                score += 3.0
            
            # Domain authority score
            if any(domain in url for domain in self.whitelist_domains):
                score += self.scoring.get('domain_authority', 1.5)
            
            # Engine score (if provided)
            score += result.get('score', 0) * 0.1
            
            result['relevance_score'] = score
        
        # Sort by relevance score (descending)
        results.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
        
        logger.debug(f"Ranked {len(results)} results")
        return results
    
    def search_multi_category(self, query: str, 
                             categories: List[str]) -> Dict[str, List[Dict]]:
        """
        Search across multiple categories
        
        Args:
            query: Search query
            categories: List of categories to search
            
        Returns:
            Dictionary mapping category to results
        """
        results_by_category = {}
        
        for category in categories:
            try:
                results = self.search(query, category=category)
                results_by_category[category] = results
            except Exception as e:
                logger.error(f"Error searching category {category}: {e}")
                results_by_category[category] = []
        
        return results_by_category
    
    def test_connection(self) -> bool:
        """
        Test connection to SearXNG
        
        Returns:
            True if connection successful
        """
        try:
            response = requests.get(
                self.base_url,
                timeout=5,
                headers={'User-Agent': 'SmartChatbot/1.0'}
            )
            
            if response.status_code == 200:
                logger.info("SearXNG connection successful")
                return True
            else:
                logger.error(f"SearXNG returned status code: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"SearXNG connection failed: {e}")
            return False
