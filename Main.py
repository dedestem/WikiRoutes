import tkinter as tk
from tkinter import messagebox
from collections import deque
from concurrent.futures import ThreadPoolExecutor, as_completed
import wikipediaapi
import json
import os
import re
from threading import Lock
import threading

# API Config
Wiki = wikipediaapi.Wikipedia('WikiRoutesMap (github.com/dedestem/wikiroutes)/1.0')
Headers = {
    'User-Agent': 'WikiRoutesBot (github.com/dedestem/wikiroutes)/1.0'
}

# Cache Config
CacheFolder = 'wikicache'
os.makedirs(CacheFolder, exist_ok=True)

# Lock for thread-safe operations
cache_lock = Lock()

def GetCacheName(Title):
    Formatted = re.sub(r'[\\\\/:*?\"<>|]', '_', Title)
    return os.path.join(CacheFolder, f"{Formatted}.json")

def GetPageLinks(Title):
    FilePath = GetCacheName(Title)

    # Check For Cache
    with cache_lock:
        if os.path.exists(FilePath):
            print(f"Pagina '{Title}' is al gecached.")
            with open(FilePath, 'r', encoding='utf-8') as f:
                return json.load(f)

    # Else fetch from the API
    Page = Wiki.page(Title)

    # Check if the page exists
    if not Page.exists():
        print(f"Pagina '{Title}' bestaat niet.")
        return []

    Links = list(Page.links.keys())

    # Save the links to cache
    with cache_lock:
        with open(FilePath, 'w', encoding='utf-8') as f:
            json.dump(Links, f, ensure_ascii=False, indent=4)

    print(f"Pagina '{Title}' is opgehaald en gecached.")
    return Links

def FindShortestWikiPath(Startpage, Endpage, stop_event):
    Queue = deque([(Startpage, [Startpage])])
    Visited = set()
    Futures = []

    def FetchLinks(Currentpage):
        return GetPageLinks(Currentpage)

    with ThreadPoolExecutor(max_workers=8) as executor:
        while Queue:
            if stop_event.is_set():
                print("Proces gestopt door gebruiker.")
                return None

            CurrentBatch = []
            for _ in range(min(len(Queue), 8)):  # Batch requests
                Currentpage, Path = Queue.popleft()
                if Currentpage == Endpage:
                    return Path
                Visited.add(Currentpage)
                CurrentBatch.append((Currentpage, Path))

            # Dispatch link fetching in parallel
            for Currentpage, Path in CurrentBatch:
                Futures.append(executor.submit(FetchLinks, Currentpage))

            for Future in as_completed(Futures):
                Links = Future.result()
                for Link in Links:
                    if Link not in Visited:
                        Queue.append((Link, Path + [Link]))
                        Visited.add(Link)

    return None  # No path found

def Start(start, goal, result_label, stop_event):
    def Target():
        Path = FindShortestWikiPath(start, goal, stop_event)
        if Path:
            result_text = "De snelste route is:\n"
            for i, Page in enumerate(Path):
                result_text += f"{i+1}. {Page}\n"
        else:
            result_text = "Geen pad gevonden."
        result_label.config(text=result_text)

    # Run the pathfinding in a separate thread to prevent blocking the GUI
    threading.Thread(target=Target, daemon=True).start()

def Stop(stop_event):
    stop_event.set()
    print("Stop signaal gegeven!")

def InitUI():
    # Create the main window
    Root = tk.Tk()
    Root.title("Wiki Routes Finder")

    # Input fields for start and goal
    start_label = tk.Label(Root, text="Startpagina:")
    start_label.pack()

    start_entry = tk.Entry(Root, width=50)
    start_entry.pack()

    goal_label = tk.Label(Root, text="Doelpuntpagina:")
    goal_label.pack()

    goal_entry = tk.Entry(Root, width=50)
    goal_entry.pack()

    # Result display
    result_label = tk.Label(Root, text="", justify=tk.LEFT)
    result_label.pack()

    # Stop event for graceful stop
    stop_event = threading.Event()

    # Start button
    start_button = tk.Button(
        Root,
        text="Start zoeken",
        command=lambda: Start(start_entry.get(), goal_entry.get(), result_label, stop_event)
    )
    start_button.pack()

    # Stop button
    stop_button = tk.Button(
        Root,
        text="Stop Zoeken",
        command=lambda: Stop(stop_event)
    )
    stop_button.pack()

    # Run the GUI
    Root.mainloop()

if __name__ == "__main__":
    InitUI()
