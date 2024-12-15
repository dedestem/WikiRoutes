import wikipediaapi
import json
import os
from collections import deque
from concurrent.futures import ThreadPoolExecutor

# Stel een aangepaste user-agent in voor de Wikipedia API-aanroepen
headers = {
    'User-Agent': 'WikiRoutesBot/1.0'  # Pas dit aan
}

# Maak een Wikipedia API object voor de Nederlandse Wikipedia
wiki = wikipediaapi.Wikipedia('WikiRoutesMap/1.0')

# Pad voor de cachemap
cache_dir = 'wikicache'
os.makedirs(cache_dir, exist_ok=True)  # Zorg dat de map bestaat

def cache_file_path(title):
    """Geeft het pad naar het cachebestand voor een specifieke pagina."""
    safe_title = title.replace("/", "_").replace(":", "_")
    return os.path.join(cache_dir, f"{safe_title}.json")


def get_page_links(title):
    """Haalt de links van een pagina op en slaat deze op in een apart cachebestand."""
    file_path = cache_file_path(title)

    # Controleer of de cache al bestaat
    if os.path.exists(file_path):
        print(f"Pagina '{title}' is al gecached.")
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    # Haal de pagina op via de API
    page = wiki.page(title)

    # Controleer of de pagina bestaat
    if not page.exists():
        print(f"Pagina '{title}' bestaat niet.")
        return []

    # Haal de links van de pagina op
    links = list(page.links.keys())

    # Sla de links op in een afzonderlijk cachebestand
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(links, f, ensure_ascii=False, indent=4)

    print(f"Pagina '{title}' is opgehaald en gecached.")
    return links

def fetch_links_concurrently(titles):
    """Haalt links van meerdere pagina's tegelijkertijd op met threading."""
    results = {}
    
    def fetch(title):
        results[title] = get_page_links(title)

    with ThreadPoolExecutor() as executor:
        executor.map(fetch, titles)

    return results

def find_shortest_path_with_cache(start_page, goal_page):
    """Zoekt het kortste pad tussen twee pagina's met behulp van BFS en caching."""
    queue = deque([(start_page, [start_page])])  # Korte pad met pagina en de route
    visited = set()  # Gevisited om herhalingen te voorkomen

    while queue:
        current_page, path = queue.popleft()

        # Check of we het doel hebben bereikt
        if current_page == goal_page:
            return path  # Return de route

        # Voeg de huidige pagina toe aan visited
        visited.add(current_page)

        # Haal de links van de huidige pagina op uit de cache
        links = get_page_links(current_page)

        # Filter links die nog niet bezocht zijn
        unvisited_links = [link for link in links if link not in visited]

        # Voeg alle unvisited links toe aan de queue
        for link in unvisited_links:
            queue.append((link, path + [link]))
            visited.add(link)

    return None  # Geen pad gevonden

# Voorbeeld gebruik
start_page = "Appel"
goal_page = "Banaan"

path = find_shortest_path_with_cache(start_page, goal_page)

if path:
    print("De snelste route is:")
    for i, page in enumerate(path):
        print(f"{i+1}. {page}")
else:
    print("Geen pad gevonden.")
