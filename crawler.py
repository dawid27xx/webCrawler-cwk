from bs4 import BeautifulSoup
from collections import Counter, deque
import requests
import json
import time
import sys
import os

BASE_URL = "https://quotes.toscrape.com"
INDEX_FILE = "../index.json"


def fetch_page(url):
    response = requests.get(url)
    return response.text

def build_index():
    index = {}
    queue = deque(['/'])
    visited_urls = set()
    
    # scrapeCounter = 0
    # while queue and scrapeCounter < 20:
    #   scrapeCounter += 1

    while queue:
        page_path = queue.popleft()
        if page_path in visited_urls:
            continue

        full_url = BASE_URL + page_path
        print(f'Crawling: {full_url}')

        html = fetch_page(full_url)
        soup = BeautifulSoup(html, 'html.parser')

        page_text = soup.get_text(separator=' ')
        words = page_text.lower().replace('.', '').replace(',', '').split()
        word_counts = Counter(words)

        for word, count in word_counts.items():
            if word not in index:
                index[word] = {full_url: count}
            else:
                index[word][full_url] = count


        visited_urls.add(page_path)

        for link in soup.find_all('a'):
            href = link.get('href')
            if href and href.startswith('/') and href not in visited_urls:
                queue.append(href)

        # time.sleep(6)

    with open(INDEX_FILE, 'w') as f:
        json.dump(index, f, indent=2)


def load_index():
    if not os.path.exists(INDEX_FILE):
        print("Index file not found. Please run the 'build' command first.")
        return None

    with open(INDEX_FILE, 'r') as f:
        return json.load(f)


def print_index(word, index):
    word = word.lower()
    if word in index:
        print(f"Inverted index for '{word}':")
        for page, freq in index[word].items():
            print(f"  {page}: {freq}")
    else:
        print(f"No entry found for '{word}'.")


def find_words(query, index):
    words = query.lower().split()
    page_scores = {}

    for word in words:
        if word in index:
            for page, freq in index[word].items():
                if page not in page_scores:
                    page_scores[page] = {'match_count': 0, 'total_freq': 0}
                page_scores[page]['match_count'] += 1
                page_scores[page]['total_freq'] += freq

    sorted_pages = sorted(
        page_scores.items(),
        key=lambda item: (item[1]['match_count'], item[1]['total_freq']),
        reverse=True
    )

    for page, _ in sorted_pages:
        print(page)

def main():
    index = None

    while True:
        user_input = input("Enter command (build, load, print [word], find [phrase], exit): ").strip()
        if not user_input:
            continue

        parts = user_input.split()
        command = parts[0].lower()

        if command == "exit":
            break
        elif command == "build":
            build_index()
            index = load_index()
        elif command == "load":
            index = load_index()
        elif command == "print":
            if len(parts) != 2:
                print("Usage: print [word]")
                continue
            if index is None:
                print("Please load or build the index first.")
                continue
            print_index(parts[1], index)
        elif command == "find":
            if len(parts) < 2:
                print("Usage: find [word or phrase]")
                continue
            if index is None:
                print("Please load or build the index first.")
                continue
            find_words(' '.join(parts[1:]), index)
        else:
            print("Unknown command.")



if __name__ == "__main__":
    main()
