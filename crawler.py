from bs4 import BeautifulSoup
from collections import Counter, deque
import requests
import json
import time
import sys
import os
import string

baseUrl = "https://quotes.toscrape.com"
indexFile = "index.json"


def buildIndex():
    invertedIndex = {}
    urlQueue = deque(['/'])
    visitedUrls = set()
    
    scrapeCounter = 0
    
    # while urlQueue: 
    while urlQueue and scrapeCounter < 20:
        scrapeCounter += 1
        pagePath = urlQueue.popleft()
        if pagePath in visitedUrls:
            continue
        
        visitedUrls.add(pagePath)

        fullUrl = baseUrl + pagePath
        print(f'Crawling: {fullUrl}')

        html = fetchPage(fullUrl)
        soup = BeautifulSoup(html, 'html.parser')

        # gets the text from the page space separated
        pageText = soup.get_text()
        
        # replaces punctuation and splits it into a list
        words = removePunctuation(pageText)

        # store the url and the positions of the words
        for pos, word in enumerate(words):
            if word not in invertedIndex:
                invertedIndex[word] = {fullUrl: [pos]}
            else:
                if fullUrl not in invertedIndex[word]:
                    invertedIndex[word][fullUrl] = [pos]
                else:
                    invertedIndex[word][fullUrl].append(pos)


        # search and add all other internal refs not in visitedUrls 
        for link in soup.find_all('a'):
            href = link.get('href')
            if href and href.startswith('/') and href not in visitedUrls:
                urlQueue.append(href)

        # time.sleep(6)

    # save to JSON file
    with open(indexFile, 'w') as f:
        json.dump(invertedIndex, f, indent=2)

def loadIndex():
    if not os.path.exists(indexFile):
        print("Index file not found. Please run the 'build' command first.")
        return None

    with open(indexFile, 'r') as f:
        return json.load(f)

def printIndex(word, invertedIndex):
    word = word.lower()
    
    # index the invertedIndex with key equal to the word
    if word in invertedIndex:
        print(f"Inverted index for '{word}':")
        for page, poss in invertedIndex[word].items():
            # tab character for clarity
            print(f"\t{page}: {poss}")
    else:
        print(f"No entry found for '{word}'.")


def findWords(query, invertedIndex):
    words = query.lower().split()
    pageScores = {}

    # scoring function --> order by match count and settle ties by total frequency = len(positions)
    for word in words:
        if word in invertedIndex:
            for page, poss in invertedIndex[word].items():
                if page not in pageScores:
                    pageScores[page] = {'matchCount': 0, 'totalFreq': 0}
                pageScores[page]['matchCount'] += 1
                pageScores[page]['totalFreq'] += len(poss)

    # sort the pages by match count settling ties by total frequency and turn into dict
    sortedPages = dict(sorted(
    pageScores.items(),
    key=lambda item: (item[1]['matchCount'], item[1]['totalFreq']),
    reverse=True
    ))

    if not sortedPages:
        print("No pages found containing any of the query words.\n")

    for page, stats in sortedPages.items():
        if stats['matchCount'] == len(words):
            print(f'\t{page} - Full Match')
        else: print(f'\t{page}')
        
def removePunctuation(text):
    cleaned = text.lower().translate(str.maketrans('', '', string.punctuation))
    return cleaned.split()

def fetchPage(url):
    response = requests.get(url)
    return response.text

def main():
    currentIndex = None

    while True:
        userInput = input("Enter command (build, load, print [word], find [phrase], exit): ").strip()
        if not userInput:
            continue

        parts = userInput.split()
        command = parts[0].lower()

        if command == "exit":
            break
        elif command == "build":
            buildIndex()
            currentIndex = loadIndex()
        elif command == "load":
            currentIndex = loadIndex()
        elif command == "print":
            if len(parts) != 2:
                print("Usage: print [word]")
                continue
            if currentIndex is None:
                print("Please load or build the index first.")
                continue
            printIndex(parts[1], currentIndex)
        elif command == "find":
            if len(parts) < 2:
                print("Usage: find [word or phrase]")
                continue
            if currentIndex is None:
                print("Please load or build the index first.")
                continue
            findWords(' '.join(parts[1:]), currentIndex)
        else:
            print("Unknown command.")


if __name__ == "__main__":
    main()
