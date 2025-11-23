import os
from typing import List, Dict
from app.logger_conf import logger
from tavily import TavilyClient
import requests

#PASTE YOUR API KEY BELOW

TAVILY_API_KEY = "" 


def tavily_search(query: str) -> List[Dict]:
    """
    TIER 1: Professional AI Search (Using Tavily API).
    """
    # Check if key is missing or still default
    if not TAVILY_API_KEY or "tvly-xxxx" in TAVILY_API_KEY:
        logger.warning("Tavily API Key is missing or invalid.")
        return []
    
    try:
        logger.info(f"Attempting Tavily search for: {query}")
        client = TavilyClient(api_key=TAVILY_API_KEY)
        
        # search_depth="basic" is faster and cheaper. Use "advanced" for deep research.
        response = client.search(
            query=query, 
            search_depth="basic", 
            max_results=5,
            include_answer=True # Tavily can generate a short direct answer too
        )
        
        results = []
        
        # 1. If Tavily provides a direct AI answer, add it as the first result
        if response.get("answer"):
            results.append({
                "title": "Direct Answer",
                "link": "Tavily AI Summary",
                "snippet": response.get("answer"),
                "source": "Tavily AI"
            })

        # 2. Add the search results
        for r in response.get("results", []):
            results.append({
                "title": r.get("title"),
                "link": r.get("url"),
                "snippet": r.get("content"),
                "source": "Tavily"
            })
        return results
    except Exception as e:
        logger.error(f"Tavily search failed: {e}")
        return []

def europe_pmc_search(query: str) -> List[Dict]:
    """
    TIER 2: Europe PMC (Fallback if Tavily quota runs out).
    """
    clean_q = query.lower().replace("latest research on", "").strip()
    logger.info(f"Attempting Europe PMC search for: {clean_q}")
    
    try:
        url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
        params = {"query": clean_q, "format": "json", "pageSize": 5}
        headers = {"User-Agent": "Mozilla/5.0"} 
        
        r = requests.get(url, params=params, headers=headers, timeout=10)
        if r.status_code != 200: return []
            
        data = r.json()
        hits = data.get("resultList", {}).get("result", [])
        
        out = []
        for h in hits:
            out.append({
                "title": h.get("title", "No Title"),
                "snippet": h.get("abstractText", "No abstract.")[:500],
                "link": f"https://europepmc.org/article/MED/{h.get('pmid', '')}",
                "source": "EuropePMC"
            })
        return out
    except Exception as e:
        logger.error(f"Europe PMC error: {e}")
        return []

def web_search_combined(query: str) -> List[Dict]:
    """
    Priority: Tavily -> Europe PMC -> Empty
    """
    # 1. Try Tavily
    res = tavily_search(query)
    if res: 
        return res

    # 2. Fallback to Europe PMC
    logger.info("Tavily failed or returned no results. Falling back to Europe PMC.")
    return europe_pmc_search(query)