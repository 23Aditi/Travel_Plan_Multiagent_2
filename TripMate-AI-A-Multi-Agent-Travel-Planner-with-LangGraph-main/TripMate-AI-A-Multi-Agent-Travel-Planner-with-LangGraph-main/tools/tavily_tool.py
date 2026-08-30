from tavily import TavilyClient
import os
from dotenv import load_dotenv
from tools.cache import tool_cache

load_dotenv()

api_key = os.getenv("TAVILY_API_KEY")
client = TavilyClient(api_key=api_key) if api_key else None

def tavily_search(query: str) -> str:
    cache_key = f"tavily:{query}"
    cached = tool_cache.get(cache_key)
    if cached is not None:
        return cached

    if not client:
        return "Tavily API key not configured. Proceeding with general knowledge recommendations."

    try:
        response = client.search(
            query=query,
            max_results=5
        )

        results = []
        for i, r in enumerate(response.get("results", []), 1):
            title = r.get("title", "Unknown")
            url = r.get("url", "")
            snippet = r.get("content", "").strip()
            if len(snippet) > 300:
                snippet = snippet[:300].rsplit(" ", 1)[0] + "..."

            results.append(f"{i}. **{title}**\n   {url}\n   {snippet}")

        formatted = "\n\n".join(results)
        tool_cache.set(cache_key, formatted, ttl=7200) # Cache for 2 hours
        return formatted
    except Exception as e:
        print(f"[tavily_search] Search error: {e}")
        return f"Hotel search encountered an issue ({e}). Proceeding with standard travel recommendations."
