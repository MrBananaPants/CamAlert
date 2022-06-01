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


# Opens all the URLs in the URLs.txt file in the browser
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
        # Clear the URLs.txt file when it's done (so the same listings won't be opened next time)
        open('URLs.txt', 'w').close()


# Function the clear all the URLs in URLs.txt
# Usefull if the list is really long like when you haven't used the app in a while
def clear_url():
    open('URLs.txt', 'w').close()


# Update the results to check for new listings
def update():
    print("UPDATING RESULTS...")
    source = requests.get(
        "https://www.2dehands.be/l/audio-tv-en-foto/fotocamera-s-analoog/#Language:all-languages|sortBy:SORT_INDEX|sortOrder:DECREASING|view:gallery-view").text
    soup = BeautifulSoup(source, 'lxml')
    # Finds all the listings on the first page
    parent = soup.find("div", {"class": "mp-Page-element mp-Page-element--main"}).find("ul")
    text = list(parent)
    dictionary = {}
    regexName = re.compile("<h3 class=\"mp-Listing-title\">(.*)</h3>")
    for findings in text:
        # Removes paid listings
        findings = findings.encode('utf-8')
        if "Topadvertentie" not in str(findings):
            advertName = regexName.search(str(findings))
            if advertName is not None:
                dictionary[advertName.group(1).encode('utf-8')] = str(findings)
    dictionaryNewListings = {}
    # Reads all the previous found listings
    file = open("output.txt", "r+")
    data = file.read()
    # Checks if the found listings are new listings that haven't been found yet
    for key in dictionary:
        if str(key) not in data:
            print("NEW LISTING: " + str(key))
            file.write(str(key) + "\n")
            dictionaryNewListings[key] = dictionary[key]
    file.close()

    fileURLs = open("URLs.txt", "a+")
    regexURL = re.compile("href=\"(.*)\"><figure class=\"mp-Listing-image-container\"")
    # Adds the URLs for the new listings to the URLs.txt file
    for key in dictionaryNewListings:
        advertURL = regexURL.search(str(dictionaryNewListings[key]))
        fileURLs.write(str(advertURL.group(1)) + "\n")
    fileURLs.close()
    # Displays a notification if there are new listings
    if len(dictionaryNewListings) > 0:
        if len(dictionaryNewListings) > 1:
            send_notification("CamAlert", "Multiple new listings")
        else:
            send_notification("CamAlert", list(dictionaryNewListings.keys())[0])
    else:
        print("NO NEW LISTINGS FOUND")
    print("RESULTS UPDATED")


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


# Start the loop (with 60 seconds interval)
threading.Thread(target=lambda: every(60)).start()
# Do an initial check for new listings when the app starts
update()


class StatusBar(rumps.App):
    @rumps.clicked("Open new listings")
    def browser(self, _):
        open_listings()

    @rumps.clicked("Clear new listings")
    def open_browser(self, _):
        clear_url()


# Display the app in the menu bar
StatusBar("CamAlert").run()
