# Smart Chatbot with SearXNG + Local LLM

Production-quality intelligent chatbot that combines the power of **SearXNG metasearch engine** with **local LLM** for accurate, source-backed AI responses.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **Smart enough to know when to search, fast enough to cache, and transparent enough to cite sources.**

## Features

✅ **Intelligent Search Decision** - Automatically determines when web search is needed  
✅ **Optimized SearXNG Integration** - Multi-engine search with result filtering and ranking  
✅ **Local LLM Support** - Works with your local LLM (OpenAI-compatible API)  
✅ **Smart Caching** - File-based cache with TTL support  
✅ **Source Citation** - Proper attribution for all web-sourced information  
✅ **Query Analysis** - Classifies queries and selects appropriate search strategies  
✅ **Production Ready** - Robust error handling, logging, and configuration  

## Architecture

```
User Query
    ↓
Query Analyzer (search needed?)
    ↓
[If Yes] → Cache Check → SearXNG Search → Result Filtering & Ranking
    ↓
Context Builder (format for LLM)
    ↓
Local LLM (generate answer)
    ↓
Response (with citations)
```

## Prerequisites

1. **SearXNG** running at `http://localhost:8080`
   - See [SearXNG Docker setup](https://github.com/searxng/searxng-docker)
   - **Important:** Enable JSON format in SearXNG settings (see setup instructions below)

2. **Local LLM** with OpenAI-compatible API
   - Examples: LM Studio, Ollama, llama.cpp, vLLM
   - Should support OpenAI-compatible `/v1/chat/completions` endpoint
   - Recommended: GPU acceleration for faster responses

3. **Python 3.8+**

## Installation

### 1. Clone Repository

```bash
git clone https://github.com/vatsalpatel1123/searxng_llm_chatbot.git
cd searxng_llm_chatbot
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Setup SearXNG (Docker)

**Enable JSON Format in SearXNG:**

Edit your SearXNG `settings.yml` file and add:

```yaml
search:
  formats:
    - html
    - json
```

Then restart SearXNG:
```bash
docker restart searxng
```

**Test JSON API:**
```bash
curl "http://localhost:8080/search?q=test&format=json"
```

### 4. Configure Chatbot

Edit `config/settings.yaml`:

```yaml
searxng:
  url: "http://127.0.0.1:8080"
  max_results: 5

llm:
  url: "http://127.0.0.1:1235/v1/chat/completions"
  model: "your-model-name"
  timeout: 120
  max_tokens: 500
```

## Quick Start

### Interactive Mode

```bash
python main.py
# Select option 7 for interactive chat
```

### Python API

```python
from src import SmartChatbot

# Initialize
bot = SmartChatbot()

# Simple usage
answer = bot.chat_simple("What's the latest news about AI?")
print(answer)

# Detailed usage
response = bot.chat("What have been the budget trends for Women & Child Welfare in MP?")
print(f"Answer: {response['answer']}")
print(f"Sources: {len(response['sources'])}")
print(f"Search used: {response['search_used']}")
```

## Usage Examples

### 1. Basic Chat

```python
bot = SmartChatbot()

# General knowledge (no search)
answer = bot.chat_simple("Explain recursion")

# Current information (with search)
answer = bot.chat_simple("Who is the current CEO of Microsoft?")
```

### 2. Get Full Response Details

```python
response = bot.chat("Latest developments in quantum computing")

print(f"Answer: {response['answer']}")
print(f"Search used: {response['search_used']}")
print(f"Cached: {response['cached']}")
print(f"Response time: {response['response_time']:.2f}s")

# View sources
for source in response['sources']:
    print(f"- {source['title']}: {source['url']}")
```

### 3. Force Search

```python
# Force search even for general questions
response = bot.chat(
    "What is machine learning?",
    force_search=True,
    max_results=5
)
```

### 4. Get Sources Only

```python
sources = bot.get_sources("artificial intelligence trends")

for source in sources:
    print(f"{source['title']}\n{source['url']}\n")
```

### 5. Cache Management

```python
# Get cache stats
stats = bot.get_stats()
print(stats['cache_stats'])

# Clear cache
bot.clear_cache()
```

## Configuration

### Key Settings

**SearXNG Configuration** (`config/settings.yaml`):

```yaml
searxng:
  url: "http://127.0.0.1:8080"
  timeout: 15
  max_results: 10
  enabled_engines:
    - google
    - bing
    - duckduckgo
    - brave
    - wikipedia
```

**LLM Configuration**:

```yaml
llm:
  url: "http://127.0.0.1:1235/v1/chat/completions"
  model: "gpt@q2_k"
  temperature: 0.7
  max_tokens: 2000
```

**Cache Configuration**:

```yaml
cache:
  enabled: true
  directory: "./cache"
  ttl:
    static_facts: 2592000  # 30 days
    news: 3600             # 1 hour
    general: 86400         # 24 hours
```

### Search Behavior

The bot automatically searches when it detects:
- Time-sensitive queries ("latest", "current", "today")
- Factual questions ("who is", "what is", "when did")
- Specific data requests ("budget", "statistics", "price")

Edit `query_analysis.search_indicators` in config to customize.

## Project Structure

```
searxng_llm_chatbot/
├── config/
│   └── settings.yaml          # All configuration
├── src/
│   ├── __init__.py
│   ├── chatbot.py            # Main chatbot class
│   ├── config.py             # Configuration manager
│   ├── query_analyzer.py     # Query analysis logic
│   ├── searxng_client.py     # SearXNG integration
│   ├── llm_client.py         # LLM integration
│   ├── context_builder.py    # Context formatting
│   └── cache_manager.py      # File-based caching
├── cache/                    # Cache storage (auto-created)
├── logs/                     # Log files (auto-created)
├── main.py                   # Examples and CLI
├── requirements.txt
└── README.md
```

## Advanced Usage

### Custom Configuration

```python
from src import SmartChatbot

bot = SmartChatbot(
    config_path="custom_config.yaml",
    cache_enabled=True,
    verbose=True  # Debug logging
)
```

### Batch Processing

```python
bot = SmartChatbot()

queries = [
    "Latest AI news",
    "MP Budget 2024",
    "Quantum computing explained"
]

for query in queries:
    response = bot.chat(query)
    print(f"Q: {query}")
    print(f"A: {response['answer']}\n")
```

### Custom Search Categories

```python
# Academic search
response = bot.chat(
    "Recent papers on neural networks",
    force_search=True
)

# News search
response = bot.chat(
    "Today's technology news",
    force_search=True
)
```

## Performance

**Typical Response Times:**
- Cached queries: <100ms ⚡
- Non-search queries: 1-3s (depends on LLM speed)
- Search queries: 3-60s (depends on LLM speed and number of results)

**Optimization Tips:**
1. ✅ **Enable caching** (default on) - Massive speedup for repeated queries
2. ⚙️ **Reduce `max_results`** (5 is optimal) - Less context = faster LLM processing
3. 🚀 **Use GPU-accelerated LLM** - 10-50x faster than CPU
4. 🔧 **Reduce `max_tokens`** (500 is good for concise answers)
5. ⏱️ **Increase `timeout`** (120s) if using slow/large models
6. 🎯 **Disable slow search engines** in config

## Troubleshooting

### SearXNG 403 Forbidden Error

**Problem:** Search requests return `403 Forbidden`

**Solution:** Enable JSON format in SearXNG settings:

```yaml
# In your SearXNG settings.yml
search:
  formats:
    - html
    - json
```

Then restart: `docker restart searxng`

### SearXNG Connection Failed

```bash
# Check if SearXNG is running
curl http://localhost:8080

# Verify URL in config/settings.yaml
searxng:
  url: "http://127.0.0.1:8080"  # Match your setup
```

### LLM Connection Failed

```bash
# Check if LLM is running
curl http://localhost:1235/v1/chat/completions

# Verify URL and model in config
llm:
  url: "http://127.0.0.1:1235/v1/chat/completions"
  model: "gpt@q2_k"  # Your model name
```

### No Search Results

- Check SearXNG engines are working
- Try different queries
- Check `searxng_client.log` for errors

### Slow Responses / LLM Timeouts

**Common causes:**
- Large/slow LLM model
- Too many search results (high `max_results`)
- CPU-only inference (no GPU)
- Too many tokens requested

**Solutions:**
1. Reduce `max_results` to 3-5 in config
2. Reduce `max_tokens` to 500 or less
3. Increase `timeout` to 120s in LLM config
4. Use GPU acceleration for your LLM
5. Use a smaller/faster model
6. Enable caching to avoid re-processing

## Logging

Logs are automatically written to console. For file logging:

```yaml
logging:
  level: "INFO"  # or DEBUG for verbose
  file: "./logs/chatbot.log"
  console: true
```

View logs:
```bash
tail -f logs/chatbot.log
```

## Testing

Run examples:
```bash
python main.py
# Select option 0 to run all examples
```

Test individual components:
```python
from src import SearXNGClient, LLMClient

# Test SearXNG
searxng = SearXNGClient(config._config)
results = searxng.search("test query")
print(f"Found {len(results)} results")

# Test LLM
llm = LLMClient(config._config)
response = llm.chat_simple("Hello")
print(response)
```

## FAQ

### Q: Why does my LLM take so long to respond?
**A:** Local LLMs can be slow, especially on CPU. Use GPU acceleration, reduce `max_tokens` (500 is good), and reduce `max_results` (5 is optimal). Caching helps a lot for repeated queries.

### Q: Can I use cloud LLMs (OpenAI, Anthropic)?
**A:** Yes! Just update the `llm.url` to point to the cloud API endpoint. Make sure to add your API key in the request headers (you may need to modify `llm_client.py`).

### Q: Why do I get 403 errors from SearXNG?
**A:** SearXNG needs JSON format enabled. Add `search: { formats: [html, json] }` to your SearXNG `settings.yml` and restart.

### Q: Can I use this without SearXNG?
**A:** The chatbot will work without search (uses only LLM knowledge), but you'll miss current information and source citations. You can disable search by setting `force_search=False`.

### Q: Which LLM models work best?
**A:** Any OpenAI-compatible model works. Recommended: Llama 3, Mistral, Qwen, Phi-3. Smaller models (7B-13B) are faster but less accurate than larger ones (70B+).

## Contributing

Contributions are welcome! Here's how you can help:

1. **Report bugs** - Open an issue with detailed steps to reproduce
2. **Suggest features** - Share your ideas in the issues
3. **Submit PRs** - Fork, make changes, and submit a pull request
4. **Improve docs** - Help make the README better

**Areas for contribution:**
- Support for more LLM providers (Gemini, Claude, etc.)
- Better result ranking algorithms
- Web UI/API server
- Streaming responses
- Multi-language support
- Performance optimizations

## Advanced Implementation Guide

For detailed research on implementing advanced LLM-powered search features, see:

[RESEARCH_LLM_SEARCH.md](RESEARCH_LLM_SEARCH.md) - Comprehensive guide covering:
- Architecture patterns (RAG, Agent-based, Hybrid)
- Search backend comparisons (SearXNG, Tavily, Brave API)
- Safety and reliability considerations
- Implementation approaches with code examples
- Cost analysis and recommendations
- Production deployment strategies

## Roadmap

- [ ] Web UI (Gradio/Streamlit)
- [ ] REST API server
- [ ] Streaming responses
- [ ] Support for more LLM providers (Tavily API integration)
- [ ] Agent-based search for complex queries
- [ ] Multi-turn conversations with context
- [ ] Vector database for semantic search
- [ ] Docker compose for easy deployment

## License

MIT License - See [LICENSE](LICENSE) file for details

Copyright (c) 2024 Vatsal Patel

## Credits

- **SearXNG** - Privacy-respecting metasearch engine ([GitHub](https://github.com/searxng/searxng))
- Built with Python, OpenAI API standards, and open-source LLMs

## Support

For issues or questions:
1. Check [Troubleshooting](#troubleshooting) section
2. Review `config/settings.yaml` configuration
3. Check logs in `logs/` directory
4. Open an issue on GitHub

## Star History

If you find this project useful, please consider giving it a ⭐ on GitHub!

---

**Made with ❤️ for accurate, source-backed AI responses**

*Privacy-focused • Open Source • Local-first*
