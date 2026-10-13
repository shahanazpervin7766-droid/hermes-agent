from duckduckgo_search import DDGS

def search_live_web(query: str, max_results: int = 5) -> str:
    """
    লাইভ গুগল / ওয়েব সার্চ করে রিয়েলটাইম ফরেক্স রেড ফোল্ডার নিউজ বা তথ্য আনে।
    """
    try:
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append(f"• {r.get('title')}: {r.get('body')}")
        
        if results:
            return "\n".join(results)
        return "কোনো সরাসরি লাইভ তথ্য পাওয়া যায়নি।"
    except Exception as e:
        print(f"Web search error: {e}")
        return f"সার্চ ত্রুটি: {str(e)}"
