"""
Main Entry Point
Examples and usage of Smart Chatbot
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src import SmartChatbot


def example_basic_usage():
    """Basic usage example"""
    print("=" * 70)
    print("EXAMPLE 1: Basic Usage")
    print("=" * 70)
    
    # Initialize chatbot
    bot = SmartChatbot(verbose=True)
    
    # Simple queries
    queries = [
        "What is Python?",  # Should NOT search
        "What's the latest news about AI?",  # Should search
        "Explain recursion in programming",  # Should NOT search
        "What have been the budget trends for Women & Child Welfare in MP Government?",  # Should search
    ]
    
    for query in queries:
        print(f"\n{'='*70}")
        print(f"Query: {query}")
        print(f"{'='*70}")
        
        response = bot.chat(query)
        
        print(f"\nSearch Used: {response['search_used']}")
        print(f"Cached: {response['cached']}")
        print(f"Response Time: {response['response_time']:.2f}s")
        print(f"\nAnswer:\n{response['answer']}")
        
        if response['sources']:
            print(f"\nSources ({len(response['sources'])}):")
            for i, source in enumerate(response['sources'], 1):
                print(f"  [{i}] {source['title']}")
                print(f"      {source['url']}")
        
        print()


def example_simple_usage():
    """Simple usage example - just get answers"""
    print("\n" + "=" * 70)
    print("EXAMPLE 2: Simple Usage (just answers)")
    print("=" * 70)
    
    bot = SmartChatbot()
    
    # Simple API - just get answer
    answer = bot.chat_simple("What is the capital of India?")
    print(f"\nQ: What is the capital of India?")
    print(f"A: {answer}")
    
    answer = bot.chat_simple("What's the weather like today?")
    print(f"\nQ: What's the weather like today?")
    print(f"A: {answer}")


def example_cache_demo():
    """Demonstrate caching"""
    print("\n" + "=" * 70)
    print("EXAMPLE 3: Cache Demonstration")
    print("=" * 70)
    
    bot = SmartChatbot()
    
    query = "Who is the current Prime Minister of India?"
    
    print(f"\nQuery: {query}")
    print("\nFirst request (no cache):")
    response1 = bot.chat(query)
    print(f"  Response Time: {response1['response_time']:.2f}s")
    print(f"  Cached: {response1['cached']}")
    
    print("\nSecond request (should use cache):")
    response2 = bot.chat(query)
    print(f"  Response Time: {response2['response_time']:.2f}s")
    print(f"  Cached: {response2['cached']}")
    
    print(f"\nAnswer: {response2['answer']}")


def example_force_search():
    """Force search even for general questions"""
    print("\n" + "=" * 70)
    print("EXAMPLE 4: Force Search")
    print("=" * 70)
    
    bot = SmartChatbot()
    
    query = "What is machine learning?"
    
    print(f"\nQuery: {query}")
    
    print("\nWithout forcing search:")
    response1 = bot.chat(query)
    print(f"  Search Used: {response1['search_used']}")
    
    print("\nWith forced search:")
    response2 = bot.chat(query, force_search=True)
    print(f"  Search Used: {response2['search_used']}")
    print(f"  Sources: {len(response2['sources'])}")


def example_get_sources_only():
    """Get just sources without generating answer"""
    print("\n" + "=" * 70)
    print("EXAMPLE 5: Get Sources Only")
    print("=" * 70)
    
    bot = SmartChatbot()
    
    query = "artificial intelligence latest developments"
    
    print(f"\nQuery: {query}")
    print("\nSources:")
    
    sources = bot.get_sources(query)
    
    for i, source in enumerate(sources[:5], 1):
        print(f"\n[{i}] {source['title']}")
        print(f"    URL: {source['url']}")
        print(f"    Snippet: {source['snippet'][:150]}...")


def example_stats():
    """Show chatbot statistics"""
    print("\n" + "=" * 70)
    print("EXAMPLE 6: Chatbot Statistics")
    print("=" * 70)
    
    bot = SmartChatbot()
    
    # Make a few queries
    bot.chat_simple("What is Python?")
    bot.chat_simple("Latest AI news")
    bot.chat_simple("Latest AI news")  # Repeat for cache
    
    stats = bot.get_stats()
    
    print("\nChatbot Stats:")
    for key, value in stats.items():
        print(f"  {key}: {value}")


def interactive_mode():
    """Interactive chat mode"""
    print("\n" + "=" * 70)
    print("INTERACTIVE MODE")
    print("=" * 70)
    print("\nType 'exit' or 'quit' to exit")
    print("Type 'cache' to show cache stats")
    print("Type 'clear' to clear cache")
    print()
    
    bot = SmartChatbot(verbose=False)
    
    while True:
        try:
            query = input("\nYou: ").strip()
            
            if not query:
                continue
            
            if query.lower() in ['exit', 'quit']:
                print("\nGoodbye!")
                break
            
            if query.lower() == 'cache':
                stats = bot.get_stats()
                print("\nCache Stats:")
                if 'cache_stats' in stats:
                    for key, value in stats['cache_stats'].items():
                        print(f"  {key}: {value}")
                continue
            
            if query.lower() == 'clear':
                bot.clear_cache()
                print("\nCache cleared!")
                continue
            
            response = bot.chat(query)
            
            print(f"\nBot: {response['answer']}")
            
            if response['sources']:
                print(f"\n[Search used, {len(response['sources'])} sources]")
            
            if response['cached']:
                print("[From cache]")
        
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}")


def main():
    """Main function"""
    print("\n" + "=" * 70)
    print("SMART CHATBOT WITH SEARXNG + LOCAL LLM")
    print("=" * 70)
    
    print("\nAvailable examples:")
    print("1. Basic usage (automated queries)")
    print("2. Simple usage (quick answers)")
    print("3. Cache demonstration")
    print("4. Force search example")
    print("5. Get sources only")
    print("6. Statistics")
    print("7. Interactive mode")
    print("0. Run all examples")
    
    choice = input("\nSelect example (0-7): ").strip()
    
    if choice == '1':
        example_basic_usage()
    elif choice == '2':
        example_simple_usage()
    elif choice == '3':
        example_cache_demo()
    elif choice == '4':
        example_force_search()
    elif choice == '5':
        example_get_sources_only()
    elif choice == '6':
        example_stats()
    elif choice == '7':
        interactive_mode()
    elif choice == '0':
        example_basic_usage()
        example_simple_usage()
        example_cache_demo()
        example_force_search()
        example_get_sources_only()
        example_stats()
    else:
        print("Invalid choice!")


if __name__ == "__main__":
    main()
