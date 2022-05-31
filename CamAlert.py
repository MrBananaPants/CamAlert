import os
import re
import threading
import time
import traceback
from pathlib import Path

import requests
import rumps
from bs4 import BeautifulSoup

# Check if the needed files exists. If not, create them
file1 = Path('output.txt')
file1.touch(exist_ok=True)
file2 = Path('URLs.txt')
file2.touch(exist_ok=True)


# Send notification function
def send_notification(title, text):
    print("Displaying notification")
    os.system("""osascript -e 'display notification "{}" with title "{}"'""".format(text, title))


def open_listings():
    baseURL = "https://www.2dehands.be"
    fileURLs = open("URLs.txt", "r")
    lines = fileURLs.readlines()
    if not lines:
        print("geen nieuwe listings")
        send_notification("CamAlert", "No new listings")
    else:
        for line in lines:
            command = "open '" + baseURL + line.rstrip() + "'"
            os.system(command)
        fileURLs.close()
        open('URLs.txt', 'w').close()


def clear_url():
    open('URLs.txt', 'w').close()


# Update the results to check for new html items
def update():
    print("UPDATING RESULTS...")
    source = requests.get(
        "https://www.2dehands.be/l/audio-tv-en-foto/fotocamera-s-analoog/#Language:all-languages|sortBy:SORT_INDEX|sortOrder:DECREASING|view:gallery-view").text
    soup = BeautifulSoup(source, 'lxml')
    parent = soup.find("div", {"class": "mp-Page-element mp-Page-element--main"}).find("ul")
    text = list(parent)
    # Removing paid adverts
    results = []
    dictionary = {}
    regexName = re.compile("<h3 class=\"mp-Listing-title\">(.*)</h3>")
    for findings in text:
        if "Topadvertentie" not in str(findings):
            advertName = regexName.search(str(findings))
            if advertName is not None:
                # print(advertName.group(1))
                # file.write(str(advertName.group(1)) + "\n")
                dictionary[advertName.group(1)] = str(findings.encode('utf-8'))
    dictionaryNewListings = {}
    file = open("output.txt", "r+")
    data = file.read()
    for key in dictionary:
        if str(key) not in data:
            print("NEW LISTING: " + str(key))
            file.write(str(key) + "\n")
            dictionaryNewListings[key] = dictionary[key]
    file.close()

    fileURLs = open("URLs.txt", "a+")
    regexURL = re.compile("href=\"(.*)\"><figure class=\"mp-Listing-image-container\"")
    for key in dictionaryNewListings:
        advertURL = regexURL.search(str(dictionaryNewListings[key]))
        fileURLs.write(str(advertURL.group(1)) + "\n")
    fileURLs.close()
    if len(dictionaryNewListings) > 0:
        if len(dictionaryNewListings) > 1:
            send_notification("CamAlert", "Multiple new listings")
        else:
            send_notification("CamAlert", list(dictionaryNewListings.keys())[0])
    else:
        print("NO NEW LISTINGS FOUND")
    print("RESULTS UPDATED")


def simulateNewResult():
    with open('output.txt', 'r') as fin:
        data = fin.read().splitlines(True)
    with open('output.txt', 'w') as fout:
        fout.writelines(data[1:])
    update()


# Run function every 60 seconds
def every(delay):
    next_time = time.time() + delay
    while True:
        time.sleep(max(0, next_time - time.time()))
        try:
            update()
        except Exception:
            traceback.print_exc()
        # skip tasks if we are behind schedule
        next_time += (time.time() - next_time) // delay * delay + delay


# send_notification("CamAlert", "App is running in the background")
threading.Thread(target=lambda: every(60)).start()
update()


class StatusBar(rumps.App):
    @rumps.clicked("Open new listings")
    def browser(self, _):
        open_listings()

    @rumps.clicked("Clear new listings")
    def open_browser(self, _):
        clear_url()


StatusBar("CamAlert").run()
