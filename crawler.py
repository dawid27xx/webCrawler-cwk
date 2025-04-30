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
        pageText = soup.get_text()
        words = removePunctuation(pageText)
        wordFreq = Counter(words)

        for word, freq in wordFreq.items():
            if word not in invertedIndex:
                invertedIndex[word] = {fullUrl: freq}
            else:
                invertedIndex[word][fullUrl] = freq


        for link in soup.find_all('a'):
            href = link.get('href')
            if href and href.startswith('/') and href not in visitedUrls and href not in urlQueue:
                urlQueue.append(href)
                
        # time.sleep(6)

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

    if word in invertedIndex:
        print(f"Frequency index for '{word}':")
        for page, freq in invertedIndex[word].items():
            print(f"\t{page}: {freq}")
    else:
        print(f"No entry found for '{word}'.")

def findWords(query, invertedIndex):
    words = query.lower().split()
    phrase = ' '.join(words)
    pageScores = {}

    for word in words:
        if word in invertedIndex:
            for page, freq in invertedIndex[word].items():
                if page not in pageScores:
                    pageScores[page] = {'matchCount': 0, 'totalFreq': 0}
                pageScores[page]['matchCount'] += 1
                pageScores[page]['totalFreq'] += freq

    if not pageScores:
        print("No pages found containing any of the query words.\n")
        return

    sortedPages = dict(sorted(
        pageScores.items(),
        key=lambda item: (item[1]['matchCount'], item[1]['totalFreq']),
        reverse=True
    ))

    fullMatchPages = [page for page, stats in sortedPages.items() if stats['matchCount'] == len(words)]
    phraseMatches = checkPhraseMatches(fullMatchPages, phrase)

    if phraseMatches:
        print(f"Pages containing the exact phrase '{phrase}':")
        for page in phraseMatches:
            print(f"\t{page} - Full Phrase Match ")

    for page, stats in sortedPages.items():
        if page in phraseMatches:
            continue 
        if stats['matchCount'] == len(words):
            print(f"\t{page} - Contains All Query Terms ")
        else:
            print(f"\t{page}")

def removePunctuation(text):
    cleaned = text.lower().translate(str.maketrans('', '', string.punctuation))
    return cleaned.split()
def fetchPage(url):
    response = requests.get(url)
    return response.text
def checkPhraseMatches(pages, phrase):
    matchedPages = []
    for page in pages:
        html = fetchPage(page)
        soup = BeautifulSoup(html, 'html.parser')
        text = soup.get_text()
        cleaned = removePunctuation(text)
        if phrase in ' '.join(cleaned):
            matchedPages.append(page)
    return matchedPages


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
