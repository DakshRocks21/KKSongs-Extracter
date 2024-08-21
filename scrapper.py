import os
import json
import requests
from bs4 import BeautifulSoup

SONGS_JSON_FILE = "songs.json"
def scrape_songs():
    base_url = "https://kksongs.org/songs/song_"
    urls = [f"{base_url}{chr(i)}.html" for i in range(ord('a'), ord('z') + 1)]
    songs = []
    
    for url in urls:
        print(f"Scraping {url}...")
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        for link in soup.find_all('a', href=True):
            print(link['href'])
            if link['href'].startswith("http://kksongs.org/songs/"):
                print(f"Found song: {link.text.strip()}")
                song_title = link.text.strip()
                songs.append({"title": song_title, "url": link['href']})

    print(f"Scraped {len(songs)} songs.")
    
    with open(SONGS_JSON_FILE, 'w') as f:
        json.dump(songs, f)
    
    return songs

def load_songs():
    if os.path.exists(SONGS_JSON_FILE):
        with open(SONGS_JSON_FILE, 'r') as f:
            return json.load(f)
    return scrape_songs()
