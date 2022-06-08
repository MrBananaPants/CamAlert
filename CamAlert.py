import os
import re
import subprocess
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
    # Check if the needed files exist. If not, create them
    output_file = Path(os.path.join(path, "output.txt"))
    output_file.touch(exist_ok=True)
    URLs_file = Path(os.path.join(path, "URLs.txt"))
    URLs_file.touch(exist_ok=True)
    blocklist_file = Path(os.path.join(path, "blocklist.txt"))
    blocklist_file.touch(exist_ok=True)
    if os.path.getsize(os.path.join(path, "blocklist.txt")) == 0:
        file = open(os.path.join(path, "blocklist.txt"), "a")
        file.write(
            "#This is the blocklist\n#To block a certain seller, brand,... you can add the name here\n#Put every word on a new line (not case sensitive)")
        file.close()


# Send notification function
def send_notification(title, text):
    print("Displaying notification")
    rumps.notification(title, None, text, data=None, sound=True)


# Opens all the URLs in the URLs.txt file in the browser
def open_listings():
    baseURL = "https://www.2dehands.be"
    fileURLs = open(os.path.join(path, "URLs.txt"), "r")
    lines = fileURLs.readlines()
    # Send notification if there are no new URLs
    if not lines:
        print("NO NEW LISTINGS")
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


def check_connection():
    try:
        request = requests.get("https://www.2dehands.be", timeout=5)
    except (requests.ConnectionError, requests.Timeout) as exception:
        print("CONNECTION ERROR")
        send_notification("CamAlert", "Connection error")
        return False
    return True


# Update the results to check for new listings
def update(show_notification=True):
    print("UPDATING RESULTS...")
    if check_connection():
        source = requests.get(
            "https://www.2dehands.be/l/audio-tv-en-foto/fotocamera-s-analoog/#Language:all-languages|sortBy:SORT_INDEX|sortOrder:DECREASING|view:gallery-view").text
        soup = BeautifulSoup(source, 'lxml')
        # Finds all the listings on the first page
        parent = soup.find("div", {"class": "mp-Page-element mp-Page-element--main"}).find("ul")
        text = list(parent)
        for index, item in enumerate(text):
            text[index] = item.encode('utf-8')
        foundListingsDictionary = {}
        regexName = re.compile("<h3 class=\"mp-Listing-title\">(.*)</h3>")
        regexURL = re.compile("href=\"(.*)\"><figure class=\"mp-Listing-image-container\"")
        blocklist_file = open(os.path.join(path, "blocklist.txt"), "r")
        blocklist_lines = blocklist_file.readlines()
        # Make a dictionary with the advert name as key and the URL as value
        for findings in text:
            blocked = False
            # Removes findings that are in the blocklist if there are any items in the blocklist
            if len(blocklist_lines) > 3:
                for line in blocklist_lines:
                    if line[0] != "#" and line.lower().rstrip() in str(findings).lower():
                        blocked = True
                        print("LISTING BLOCKED BECAUSE OF BLOCKLIST WORD: " + line.lower())
                if not blocked:
                    advertName = regexName.search(str(findings))
                    advertURL = regexURL.search(str(findings))
                    if advertName is not None:
                        foundListingsDictionary[advertName.group(1)] = str(advertURL.group(1))
            # If there are no items in the blocklist:
            else:
                advertName = regexName.search(str(findings))
                advertURL = regexURL.search(str(findings))
                if advertName is not None:
                    foundListingsDictionary[advertName.group(1)] = str(advertURL.group(1))

        newListingsDictionary = {}
        # Reads all the previous found listings
        file = open(os.path.join(path, "output.txt"), "r+")
        previousListings = file.readlines()
        first_install = bool(os.path.getsize(os.path.join(path, "output.txt")) == 0)
        if first_install:
            print("FIRST INSTALL")
        # Checks if the found listings are new listings that haven't been found yet
        for key in foundListingsDictionary:
            if str(key) + ";URL:" + str(foundListingsDictionary[key]) not in previousListings:
                print("NEW LISTING: " + str(key))
                file.write(str(key) + ";URL:" + str(foundListingsDictionary[key]) + "\n")
                newListingsDictionary[key] = foundListingsDictionary[key]
        file.close()
        fileURLs = open(os.path.join(path, "URLs.txt"), "a+")
        # Adds the URLs for the new listings to the URLs.txt file
        for key in newListingsDictionary:
            fileURLs.write(str(newListingsDictionary[key]) + "\n")
        fileURLs.close()
        # Displays a notification if there are new listings
        if len(newListingsDictionary) > 0 and not first_install:
            if len(newListingsDictionary) > 1:
                print("multiple new listings")
                if show_notification:
                    send_notification("CamAlert", "Multiple new listings")
            # There's 1 new listing
            else:
                print("1 new listing")
                if show_notification:
                    send_notification("CamAlert", list(newListingsDictionary.keys())[0])
        # There are no new listings
        elif not first_install:
            print("NO NEW LISTINGS FOUND")
        # It's the first install of the app, display an alert
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
    data = file.readlines()
    print("len(data) = " + str(len(data)))
    if len(data) == 1:
        send_notification("CamAlert", "1 new listing")
    elif len(data) > 1:
        send_notification("CamAlert", "Multiple new listings")
    else:
        send_notification("CamAlert", "No new listings")
    file.close()


# Clears the output and URLs file
def reset_camalert():
    open(os.path.join(path, "output.txt"), 'w').close()
    open(os.path.join(path, "URLs.txt"), 'w').close()
    # open(os.path.join(path, "blocklist.txt"), 'w').close()


def open_blocklist():
    subprocess.call(['open', '-a', 'TextEdit', os.path.join(path, "blocklist.txt")])


# Run update function every 60 seconds
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
    def __init__(self):
        super(StatusBar, self).__init__("CamAlert")
        self.menu = ["Open new listings", "Clear new listings", None, "Manual update", None, ["Settings", ["Blocklist", "Reset"]]]

    @rumps.clicked("Open new listings")
    def browser(self, _):
        open_listings()

    @rumps.clicked("Clear new listings")
    def open_browser(self, _):
        clear_url()

    @rumps.clicked("Manual update")
    def manual(self, _):
        if check_connection():
            manual_update()

    @rumps.clicked("Settings", "Blocklist")
    def blocklist(self, _):
        open_blocklist()

    @rumps.clicked("Settings", "Reset")
    def reset(self, _):
        reset_camalert()
        check_files()
        update(False)

    @rumps.notifications
    def notifications(self, _):  # function that reacts to incoming notification dicts
        open_listings()


# Start the loop (with 60 seconds interval)
threading.Thread(target=lambda: every(60)).start()
# Do an initial check for new listings when the app starts
check_files()
update()

# Display the app in the menu bar
StatusBar().run()
