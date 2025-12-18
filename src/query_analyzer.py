"""
Query Analyzer Module
Intelligently determines when web search is needed
"""

import re
from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)


class QueryAnalyzer:
    """Analyzes queries to determine if web search is needed"""
    
    def __init__(self, config: Dict):
        """
        Initialize query analyzer
        
        Args:
            config: Configuration dictionary with search indicators
        """
        self.search_indicators = config.get('query_analysis', {}).get('search_indicators', {})
        self.no_search_indicators = config.get('query_analysis', {}).get('no_search_indicators', [])
        self.min_query_length = config.get('query_analysis', {}).get('min_query_length', 5)
        
        # Compile regex patterns for efficiency
        self._compile_patterns()
        
        logger.info("Query analyzer initialized")
    
    def _compile_patterns(self):
        """Compile regex patterns for quick matching"""
        # Time-sensitive patterns
        self.time_patterns = [
            r'\b(latest|current|today|now|recent|this (week|month|year))\b',
            r'\b(yesterday|tomorrow)\b',
            r'\b\d{4}\b',  # Year numbers
        ]
        
        # Question patterns
        self.question_patterns = [
            r'^(who|what|when|where|which|whose|whom)\b',
            r'\b(how many|how much)\b',
        ]
        
        # Specific data patterns
        self.data_patterns = [
            r'\b(price|cost|salary|budget|statistics|data|number)\b',
            r'\b(weather|temperature|forecast)\b',
            r'\b(stock|market|exchange)\b',
        ]
        
        # Compile all patterns
        self.compiled_time_patterns = [re.compile(p, re.IGNORECASE) for p in self.time_patterns]
        self.compiled_question_patterns = [re.compile(p, re.IGNORECASE) for p in self.question_patterns]
        self.compiled_data_patterns = [re.compile(p, re.IGNORECASE) for p in self.data_patterns]
    
    def needs_search(self, query: str) -> Tuple[bool, str]:
        """
        Determine if query needs web search
        
        Args:
            query: User query
            
        Returns:
            Tuple of (needs_search: bool, reason: str)
        """
        # Basic validation
        if not query or len(query.strip()) < self.min_query_length:
            return False, "Query too short"
        
        query_lower = query.lower().strip()
        
        # Check for explicit search indicators
        for category, keywords in self.search_indicators.items():
            for keyword in keywords:
                if keyword.lower() in query_lower:
                    logger.debug(f"Search needed: matched '{keyword}' in category '{category}'")
                    return True, f"Time-sensitive/factual query ({keyword})"
        
        # Check time-sensitive patterns
        for pattern in self.compiled_time_patterns:
            if pattern.search(query_lower):
                logger.debug(f"Search needed: matched time pattern")
                return True, "Time-sensitive query"
        
        # Check question patterns (who, what, when, where)
        for pattern in self.compiled_question_patterns:
            if pattern.search(query_lower):
                # Additional check: is it asking about a specific entity?
                if self._is_specific_entity_question(query_lower):
                    logger.debug(f"Search needed: specific entity question")
                    return True, "Specific entity question"
        
        # Check for specific data requests
        for pattern in self.compiled_data_patterns:
            if pattern.search(query_lower):
                logger.debug(f"Search needed: specific data request")
                return True, "Specific data request"
        
        # Check for no-search indicators (explanations, tutorials)
        for indicator in self.no_search_indicators:
            if indicator.lower() in query_lower:
                logger.debug(f"Search not needed: matched '{indicator}'")
                return False, f"General knowledge query ({indicator})"
        
        # Default: check if it seems like a current/specific question
        if self._appears_current_specific(query_lower):
            logger.debug(f"Search needed: appears current/specific")
            return True, "Appears to be current/specific query"
        
        logger.debug(f"Search not needed: general knowledge query")
        return False, "General knowledge query"
    
    def _is_specific_entity_question(self, query: str) -> bool:
        """
        Check if question is about a specific entity
        
        Args:
            query: Query string
            
        Returns:
            True if asking about specific entity
        """
        # Patterns indicating specific entity questions
        specific_patterns = [
            r'who is [A-Z]',  # "who is John Doe"
            r'what is the .* of',  # "what is the capital of"
            r'when did .* happen',  # "when did X happen"
            r'where is .* located',  # "where is X located"
        ]
        
        for pattern in specific_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                return True
        
        # Check for proper nouns (capitalized words)
        words = query.split()
        capitalized_words = [w for w in words if w and w[0].isupper() and len(w) > 2]
        
        # If query has 2+ capitalized words, likely asking about specific entity
        if len(capitalized_words) >= 2:
            return True
        
        return False
    
    def _appears_current_specific(self, query: str) -> bool:
        """
        Check if query appears to be asking for current/specific information
        
        Args:
            query: Query string
            
        Returns:
            True if appears current/specific
        """
        # Check for specific organizations, places, people
        proper_noun_indicators = [
            'government', 'ministry', 'department', 'company', 'organization',
            'madhya pradesh', 'mp', 'india', 'indian'
        ]
        
        for indicator in proper_noun_indicators:
            if indicator in query:
                return True
        
        # Check for numbers/years
        if re.search(r'\b20\d{2}\b', query):  # Years like 2024
            return True
        
        # Check for specific metrics
        if re.search(r'\b\d+\s*(percent|%|crore|lakh|million|billion)\b', query):
            return True
        
        return False
    
    def classify_query_type(self, query: str) -> str:
        """
        Classify query into type
        
        Args:
            query: User query
            
        Returns:
            Query type: 'news', 'academic', 'general', 'technical', etc.
        """
        query_lower = query.lower()
        
        # News queries
        if any(word in query_lower for word in ['news', 'latest', 'breaking', 'today']):
            return 'news'
        
        # Academic queries
        if any(word in query_lower for word in ['research', 'study', 'paper', 'journal', 'academic']):
            return 'academic'
        
        # Technical queries
        if any(word in query_lower for word in ['code', 'programming', 'error', 'debug', 'api']):
            return 'technical'
        
        # Statistical queries
        if any(word in query_lower for word in ['statistics', 'data', 'numbers', 'graph', 'chart']):
            return 'statistical'
        
        # Default
        return 'general'
    
    def get_search_category(self, query: str) -> str:
        """
        Get appropriate search category for query
        
        Args:
            query: User query
            
        Returns:
            Category: 'general', 'news', 'academic', 'technical'
        """
        query_type = self.classify_query_type(query)
        
        # Map query types to search categories
        category_map = {
            'news': 'news',
            'academic': 'academic',
            'technical': 'technical',
            'statistical': 'general',
            'general': 'general'
        }
        
        return category_map.get(query_type, 'general')
    
    def analyze(self, query: str) -> Dict:
        """
        Comprehensive query analysis
        
        Args:
            query: User query
            
        Returns:
            Dictionary with analysis results
        """
        needs_search, reason = self.needs_search(query)
        query_type = self.classify_query_type(query)
        category = self.get_search_category(query)
        
        analysis = {
            'needs_search': needs_search,
            'reason': reason,
            'query_type': query_type,
            'search_category': category,
            'query_length': len(query),
            'is_question': any(p.search(query) for p in self.compiled_question_patterns)
        }
        
        logger.info(f"Query analysis: {analysis}")
        
        return analysis
