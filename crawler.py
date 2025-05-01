from bs4 import BeautifulSoup
from collections import Counter, deque
import requests
import json
import time
import sys
import os
import re
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
        pageText = soup.get_text()
        words = removePunctuation(pageText)

        for pos, word in enumerate(words):
            if word not in invertedIndex:
                invertedIndex[word] = {fullUrl: [pos]}
            else:
                if fullUrl not in invertedIndex[word]:
                    invertedIndex[word][fullUrl] = [pos]
                else:
                    invertedIndex[word][fullUrl].append(pos)

        for link in soup.find_all('a'):
            href = link.get('href')
            if href and href.startswith('/') and href not in visitedUrls and href not in urlQueue:
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
            print(f"\t{page}: {poss}")
    else:
        print(f"No entry found for '{word}'.")

def findWords(query, invertedIndex):
    words = query.lower().split()
    pageScores = {}

    for word in words:
        if word in invertedIndex:
            for page, positions in invertedIndex[word].items():
                stats = pageScores.setdefault(page, {'matchCount': 0, 'totalFreq': 0})
                stats['matchCount'] += 1
                stats['totalFreq'] += len(positions)

    if not pageScores:
        print("No pages found containing any of the query words.\n")
        return
    
    candidatePhraseMatchPages = [page for page, stats in pageScores.items() if stats['matchCount'] == len(words)]
    
    subPhrases = computeSubPhrases(query)

    # exact full phrase matches
    exactPages = set(phraseMatch(query, invertedIndex, candidatePhraseMatchPages))

    # subphrase matches that are not exact
    subphrasePages = {}
    for subphrase in subPhrases:
        matches = phraseMatch(subphrase, invertedIndex, candidatePhraseMatchPages)
        for p in matches:
            if p not in exactPages:
                subphrasePages.setdefault(p, set()).add(subphrase)

    # general word matches exclude pages in above categories
    generalPages = {
    p: stats for p, stats in pageScores.items()
    if p not in exactPages and p not in subphrasePages
    }


    # Output in order:
    print("Results:")

    for p in sorted(exactPages, key=lambda p: (pageScores[p]['matchCount'], pageScores[p]['totalFreq']), reverse=True):
        stats = pageScores[p]
        print(f'\t{p} - Exact phrase match (matchCount={stats["matchCount"]}, totalFreq={stats["totalFreq"]})')

    for p in sorted(subphrasePages, key=lambda p: (pageScores[p]['matchCount'], pageScores[p]['totalFreq']), reverse=True):
        stats = pageScores[p]
        phrases_str = ', '.join(sorted(subphrasePages[p]))
        print(f'\t{p} - Subphrase match: {phrases_str} (matchCount={stats["matchCount"]}, totalFreq={stats["totalFreq"]})')


    for p, stats in sorted(generalPages.items(), key=lambda item: (item[1]['matchCount'], item[1]['totalFreq']), reverse=True):
        print(f'\t{p} - Partial word match (matchCount={stats["matchCount"]}, totalFreq={stats["totalFreq"]})')

def computeSubPhrases(query):
    words = query.split()
    n = len(words)
    subphrases = []

    for length in range(2, n): 
        for start in range(n - length + 1):
            subphrase = ' '.join(words[start:start + length])
            subphrases.append(subphrase)

    return subphrases

def checkSubPhrases(subphrase, invertedIndex, pages):
    pages = phraseMatch(subphrase, invertedIndex, pages)
    if not pages:
        return 0
    else: return pages
    
def phraseMatch(phrase, invertedIndex, candidatePages):
    words = phrase.lower().split()
    exactPages = []
    
    for page in candidatePages:
        # Collect positions for each word
        word_positions = []
        for word in words:
            positions = invertedIndex.get(word, {}).get(page, [])
            word_positions.append(set(positions))
        
        # Check for sequence of positions
        possible_starts = word_positions[0]
        for start_pos in possible_starts:
            if all((start_pos + offset) in word_positions[offset] for offset in range(1, len(words))):
                exactPages.append(page)
                break  # No need to check other positions
    return exactPages

def removePunctuation(text):
    # https://www.jeremymorgan.com/python/how-to-remove-punctuation-from-a-string-python/#:~:text=We%20use%20the%20re.,other%20non%2Dpunctuating%20Unicode%20characters.
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)
    return text.strip().split()

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