from __future__ import annotations
from pathlib import Path
from langchain_core.tools import tool

@tool
def fetch_company_info(category: str) -> str:
    """Fetch static company information from the knowledge base.
    
    Use this tool for simple queries about NOM's services, contact info, pricing, 
    team, or general about info. This is faster than rag_search.
    
    Args:
        category: The type of information to fetch. 
                 Options: 'about', 'contact', 'faq', 'how-we-work', 'pricing', 'services', 'team', 'technology-stack'.
    """
    # Mapping human-friendly names to filenames
    mapping = {
        "about": "about.md",
        "contact": "contact.md",
        "faq": "faq.md",
        "how-we-work": "how-we-work.md",
        "pricing": "pricing.md",
        "services": "services.md",
        "team": "team.md",
        "technology-stack": "technology-stack.md",
    }
    
    # Normalize input: lowercase and replace underscores with hyphens
    category_normalized = category.lower().strip().replace("_", "-")
    filename = mapping.get(category_normalized)
    
    if not filename:
        return f"Invalid category: '{category}'. Available categories: {', '.join(mapping.keys())}"
    
    # Path relative to this file: backend/agent/tools/company_info.py
    # KB is at: backend/kb/company/
    base_dir = Path(__file__).parent.parent.parent / "kb" / "company"
    file_path = base_dir / filename
    
    try:
        if not file_path.exists():
             return f"Company information for '{category}' (file: {filename}) not found."
             
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            if not content.strip():
                return f"The information for '{category}' is currently empty."
            return content
    except Exception as e:
        return f"Error reading company information: {str(e)}"
