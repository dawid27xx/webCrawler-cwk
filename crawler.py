from bs4 import BeautifulSoup
from collections import Counter, deque
import requests
import json
import time
import sys
import os

BASE_URL = "https://quotes.toscrape.com"
INDEX_FILE = "index.json"

# Function: Fetch HTML from a URL
def fetch_page(url):
    response = requests.get(url)
    return response.text

# Function: Parse HTML content and extract words to update index
def parse_quotes(html, url, index):
    """
    Parses HTML content, extracts quotes, splits into words,
    updates the inverted index with word frequencies per page.
    """
    pass  # Implement BeautifulSoup parsing and index updating

def build_index():
    index = {}
    queue = deque(['/'])
    visited_urls = set()
    # scrapeCounter = 0

    # while queue and scrapeCounter < 20:
    while queue:
        # scrapeCounter += 1
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
                index[word] = {}
            if full_url not in index[word]:
                index[word][full_url] = 0
            index[word][full_url] += count

        visited_urls.add(page_path)

        for link in soup.find_all('a'):
            href = link.get('href')
            if href and href.startswith('/') and href not in visited_urls:
                queue.append(href)

        # time.sleep(6)
    # print(index)
    with open(INDEX_FILE, 'w') as f:
        json.dump(index, f, indent=2)

    print("Index successfully built and saved to", INDEX_FILE)

# Function: Load the existing inverted index from a JSON file
def load_index():
    """
    Checks if an index file exists, and loads the inverted index into memory.
    """
    pass  # Implement JSON loading

# Function: Print the inverted index entry for a specific word
def print_index(word, index):
    """
    Given a word, prints all pages it appears in and the frequency per page.
    """
    pass  # Implement word lookup and printing logic

# Function: Find pages containing single or multiple words
def find_words(query, index):
    """
    Finds all pages containing all words in the query and prints them.
    """
    pass  # Implement multi-word intersection logic

# Main CLI function to handle commands
def main():
    build_index()
    """
    Parses command-line arguments to execute one of:
    - build
    - load
    - print [word]
    - find [word or phrase]
    """
    pass  # Implement argument parsing and function calling

if __name__ == "__main__":
    main()
