from collections import deque
from concurrent.futures import ThreadPoolExecutor
import wikipediaapi
import json
import os
import re

# API Config
Wiki = wikipediaapi.Wikipedia('WikiRoutesMap (github.com/dedestem/wikiroutes)/1.0')
Headers = {
    'User-Agent': 'WikiRoutesBot (github.com/dedestem/wikiroutes)/1.0'
}

# Cache Config
CacheFolder = 'wikicache'
os.makedirs(CacheFolder, exist_ok=True)


def GetCacheName(Title):
    Formatted = re.sub(r'[\\\\/:*?\"<>|]', '_', Title)
    return os.path.join(CacheFolder, f"{Formatted}.json")

def GetPageLinks(Title):
    FilePath = GetCacheName(Title)

    # Check For Cache
    if os.path.exists(FilePath):
        print(f"Pagina '{Title}' is al gecached.")
        with open(FilePath, 'r', encoding='utf-8') as f:
            return json.load(f)

    # Anders haal info op via API
    Page = Wiki.page(Title)

    # Check of de pagina bestaat
    if not Page.exists():
        print(f"Pagina '{Title}' bestaat niet.")
        return []

    Links = list(Page.links.keys())

    # Sla de links op in een afzonderlijk cachebestand
    with open(FilePath, 'w', encoding='utf-8') as f:
        json.dump(Links, f, ensure_ascii=False, indent=4)

    print(f"Pagina '{Title}' is opgehaald en gecached.")
    return Links

def FetchLinksThreaded(Titles):
    Results = {}
    
    def Fetch(Title):
        Results[Title] = GetPageLinks(Title)

    with ThreadPoolExecutor() as executor:
        executor.map(Fetch, Titles)

    return Results

def FindShortestWikiPath(Startpage, Endpage):
    Queue = deque([(Startpage, [Startpage])])
    Visited = set()

    while Queue:
        Currentpage, Path = Queue.popleft()

        if Currentpage == Endpage:
            return Path

        # Voeg de huidige pagina toe aan visited
        Visited.add(Currentpage)

        # Haal de links van de huidige pagina op uit de cache
        Links = GetPageLinks(Currentpage)

        # Filter links die nog niet bezocht zijn
        UnvisitedLinks = [Link for Link in Links if Link not in Visited]

        # Voegt alle links die nog niet bezocht zijn aan de queue
        for Link in UnvisitedLinks:
            Queue.append((Link, Path + [Link]))
            Visited.add(Link)

    return None  # Geen pad gevonden

# Start

Startpage = "Appel"
Goalpage = "Banaan"

Path = FindShortestWikiPath(Startpage, Goalpage)

if Path:
    print("De snelste route is:")
    for i, Page in enumerate(Path):
        print(f"{i+1}. {Page}")
else:
    print("Geen pad gevonden.")
