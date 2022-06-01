import os
import re
import threading
import time
import traceback
from pathlib import Path

import requests
import rumps
from bs4 import BeautifulSoup

path = os.path.join(os.getenv("HOME"), "CamAlert")


def check_files():
    # Check whether the specified path exists or not
    if not os.path.exists(path):
        os.makedirs(path)
        print("DIRECTORY CREATED")
    # Check if the needed files exists. If not, create them
    file1 = Path(os.path.join(path, "output.txt"))
    file1.touch(exist_ok=True)
    file2 = Path(os.path.join(path, "URLs.txt"))
    file2.touch(exist_ok=True)


# Send notification function
def send_notification(title, text):
    print("Displaying notification")
    rumps.notification(title, None, text, data=None, sound=True)


# Opens all the URLs in the URLs.txt file in the browser
def open_listings():
    baseURL = "https://www.2dehands.be"
    fileURLs = open(os.path.join(path, "URLs.txt"), "r")
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
        open(os.path.join(path, "URLs.txt"), 'w').close()


# Function the clear all the URLs in URLs.txt
# Usefull if the list is really long like when you haven't used the app in a while
def clear_url():
    open(os.path.join(path, "URLs.txt"), 'w').close()


# Update the results to check for new listings
def update(show_notification=True):
    print("UPDATING RESULTS...")
    source = requests.get(
        "https://www.2dehands.be/l/audio-tv-en-foto/fotocamera-s-analoog/#Language:all-languages|sortBy:SORT_INDEX|sortOrder:DECREASING|view:gallery-view").text
    soup = BeautifulSoup(source, 'lxml')
    # Finds all the listings on the first page
    parent = soup.find("div", {"class": "mp-Page-element mp-Page-element--main"}).find("ul")
    text = list(parent)
    for index, item in enumerate(text):
        text[index] = item.encode('utf-8')
    dictionary = {}
    regexName = re.compile("<h3 class=\"mp-Listing-title\">(.*)</h3>")
    for findings in text:
        # Removes paid listings
        if "Topadvertentie" not in str(findings):
            advertName = regexName.search(str(findings))
            if advertName is not None:
                dictionary[advertName.group(1)] = str(findings)
    dictionaryNewListings = {}
    # Reads all the previous found listings
    file = open(os.path.join(path, "output.txt"), "r+")
    data = file.read()
    first_install = bool(os.path.getsize(os.path.join(path, "output.txt")) == 0)
    if first_install:
        print("FIRST INSTALL")
    # Checks if the found listings are new listings that haven't been found yet
    for key in dictionary:
        if str(key) not in data:
            print("NEW LISTING: " + str(key))
            file.write(str(key) + "\n")
            dictionaryNewListings[key] = dictionary[key]
    file.close()

    fileURLs = open(os.path.join(path, "URLs.txt"), "a+")
    regexURL = re.compile("href=\"(.*)\"><figure class=\"mp-Listing-image-container\"")
    # Adds the URLs for the new listings to the URLs.txt file
    for key in dictionaryNewListings:
        advertURL = regexURL.search(str(dictionaryNewListings[key]))
        fileURLs.write(str(advertURL.group(1)) + "\n")
    fileURLs.close()
    # Displays a notification if there are new listings
    if len(dictionaryNewListings) > 0 and not first_install:
        if len(dictionaryNewListings) > 1:
            print("multiple new listings")
            if show_notification:
                send_notification("CamAlert", "Multiple new listings")
        else:
            print("1 new listing")
            if show_notification:
                send_notification("CamAlert", list(dictionaryNewListings.keys())[0])
    elif not first_install:
        print("NO NEW LISTINGS FOUND")
    else:
        rumps.alert(title="CamAlert",
                    message="Thank you for using CamAlert. The app will periodically check for new listings. If it finds one, it will send you a notification.",
                    ok=None, cancel=None)
        clear_url()
    print("RESULTS UPDATED")


# Manual update disables the notifications from update() because it checks if there are older unseen listings in the URLs.txt file
# and sends a notification accordingly
# This makes sure the user won't get a notification saying there's 1 new listings but when he opens the new listings, it'll open more than 1 listing
def manual_update():
    update(False)
    file = open(os.path.join(path, "URLs.txt"), "r+")
    data = file.read()
    if len(data) == 1:
        send_notification("CamAlert", "1 new listing")
    if len(data) > 1:
        send_notification("CamAlert", "Multiple new listings")
    else:
        send_notification("CamAlert", "No new listings")
    file.close()


def reset_camalert():
    open(os.path.join(path, "output.txt"), 'w').close()
    open(os.path.join(path, "URLs.txt"), 'w').close()


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


class StatusBar(rumps.App):
    @rumps.clicked("Open new listings")
    def browser(self, _):
        open_listings()

    @rumps.clicked("Clear new listings")
    def open_browser(self, _):
        clear_url()

    @rumps.clicked("Manual update")
    def manual(self, _):
        manual_update()

    @rumps.clicked("Reset")
    def reset(self, _):
        reset_camalert()
        check_files()
        update(False)


# Start the loop (with 60 seconds interval)
threading.Thread(target=lambda: every(60)).start()
# Do an initial check for new listings when the app starts
check_files()
update()

# Display the app in the menu bar
StatusBar("CamAlert").run()
