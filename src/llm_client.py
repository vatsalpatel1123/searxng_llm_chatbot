"""
LLM Client Module
Client for interacting with local LLM
"""

import requests
from typing import List, Dict, Optional, Any
import logging
import json

logger = logging.getLogger(__name__)


class LLMClient:
    """Client for local LLM with OpenAI-compatible API"""
    
    def __init__(self, config: Dict):
        """
        Initialize LLM client
        
        Args:
            config: Configuration dictionary
        """
        self.base_url = config.get('llm', {}).get('url', 'http://localhost:1235/v1/chat/completions')
        self.model = config.get('llm', {}).get('model', 'gpt@q2_k')
        self.temperature = config.get('llm', {}).get('temperature', 0.7)
        self.max_tokens = config.get('llm', {}).get('max_tokens', 2000)
        self.timeout = config.get('llm', {}).get('timeout', 30)
        
        self.default_system_prompt = config.get('llm', {}).get('default_system_prompt', 
                                                               'You are a helpful AI assistant.')
        self.search_system_prompt = config.get('llm', {}).get('search_system_prompt',
                                                              'You are a helpful AI assistant with web search.')
        
        logger.info(f"LLM client initialized (Model: {self.model})")
    
    def chat(self, messages: List[Dict[str, str]], 
             temperature: Optional[float] = None,
             max_tokens: Optional[int] = None) -> str:
        """
        Send chat completion request to LLM
        
        Args:
            messages: List of message dictionaries
            temperature: Override default temperature
            max_tokens: Override default max tokens
            
        Returns:
            LLM response text
        """
        if temperature is None:
            temperature = self.temperature
        
        if max_tokens is None:
            max_tokens = self.max_tokens
        
        payload = {
            'model': self.model,
            'messages': messages,
            'temperature': temperature,
            'max_tokens': max_tokens,
            'stream': False
        }
        
        try:
            logger.debug(f"Sending request to LLM with {len(messages)} messages")
            
            response = requests.post(
                self.base_url,
                json=payload,
                timeout=self.timeout,
                headers={'Content-Type': 'application/json'}
            )
            
            response.raise_for_status()
            data = response.json()
            
            # Extract response text
            if 'choices' in data and len(data['choices']) > 0:
                message = data['choices'][0].get('message', {})
                content = message.get('content', '')
                
                logger.debug(f"Received LLM response ({len(content)} chars)")
                return content
            else:
                logger.error("Invalid response format from LLM")
                return "Sorry, I couldn't generate a response."
                
        except requests.exceptions.Timeout:
            logger.error(f"LLM request timeout after {self.timeout}s")
            return "Sorry, the request timed out. Please try again."
        except requests.exceptions.RequestException as e:
            logger.error(f"LLM request error: {e}")
            return f"Sorry, an error occurred: {str(e)}"
        except (ValueError, KeyError) as e:
            logger.error(f"Error parsing LLM response: {e}")
            return "Sorry, I couldn't process the response."
    
    def chat_simple(self, user_message: str, 
                   system_prompt: Optional[str] = None) -> str:
        """
        Simple chat with user message
        
        Args:
            user_message: User's message
            system_prompt: Optional system prompt (uses default if None)
            
        Returns:
            LLM response
        """
        if system_prompt is None:
            system_prompt = self.default_system_prompt
        
        messages = [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_message}
        ]
        
        return self.chat(messages)
    
    def chat_with_context(self, user_message: str, 
                         search_context: str) -> str:
        """
        Chat with search context
        
        Args:
            user_message: User's message
            search_context: Search results context
            
        Returns:
            LLM response
        """
        # Build enhanced prompt with context
        enhanced_prompt = f"""{user_message}

{search_context}

Please provide a comprehensive answer based on the search results above. Make sure to:
1. Cite sources using [1], [2], etc. when stating facts
2. Synthesize information from multiple sources when relevant
3. Mention if information is recent or might change
4. Keep the response clear and well-organized"""
        
        messages = [
            {'role': 'system', 'content': self.search_system_prompt},
            {'role': 'user', 'content': enhanced_prompt}
        ]
        
        return self.chat(messages)
    
    def test_connection(self) -> bool:
        """
        Test connection to LLM
        
        Returns:
            True if connection successful
        """
        try:
            test_messages = [
                {'role': 'system', 'content': 'You are a helpful assistant.'},
                {'role': 'user', 'content': 'Say "OK" if you can hear me.'}
            ]
            
            response = self.chat(test_messages, max_tokens=10)
            
            if response and len(response) > 0:
                logger.info("LLM connection successful")
                return True
            else:
                logger.error("LLM returned empty response")
                return False
                
        except Exception as e:
            logger.error(f"LLM connection test failed: {e}")
            return False
    
    def estimate_tokens(self, text: str) -> int:
        """
        Rough estimate of token count
        
        Args:
            text: Text to estimate
            
        Returns:
            Estimated token count
        """
        # Rough estimate: ~4 characters per token
        return len(text) // 4
