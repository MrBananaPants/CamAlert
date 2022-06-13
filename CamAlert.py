import http.client as httplib
import json
import os
import subprocess
import threading
import time
import traceback
from pathlib import Path

import requests
import rumps

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
    lines = fileURLs.read().splitlines()
    fileURLs.close()
    # Send notification if there are no new URLs
    if not lines:
        print("NO NEW LISTINGS")
        send_notification("CamAlert", "No new listings")
    else:
        if len(lines) >= 10:
            if rumps.alert(title="CamAlert", message=f'{len(lines)} tabs will be opened. Do you want to continue?', ok=None, cancel=True) == 1:
                for line in lines:
                    command = "open '" + baseURL + line + "'"
                    os.system(command)
                    # Clear the URLs.txt file when it's done (so the same listings won't be opened next time)
                    open(os.path.join(path, "URLs.txt"), 'w').close()
        else:
            for line in lines:
                command = "open '" + baseURL + line + "'"
                os.system(command)
                # Clear the URLs.txt file when it's done (so the same listings won't be opened next time)
                open(os.path.join(path, "URLs.txt"), 'w').close()


# Function the clear all the URLs in URLs.txt
# Usefull if the list is really long like when you haven't used the app in a while
def clear_url():
    open(os.path.join(path, "URLs.txt"), 'w').close()


def check_connection():
    connection = httplib.HTTPConnection("www.2dehands.be", timeout=7)
    try:
        # only header requested for fast operation
        connection.request("HEAD", "/")
        connection.close()
        print("Internet On")
        return True
    except Exception as exep:
        print(exep)
        return False


# Update the results to check for new listings
def update(show_notification=True):
    print("UPDATING RESULTS...")
    if check_connection():
        foundListingsDictionary = {}
        numberOfListings = 50
        source = requests.get(
            f"https://www.2dehands.be/lrp/api/search?attributesByKey\\[\\]=Language%3Aall-languages&l1CategoryId=31&l2CategoryId=480&limit={numberOfListings}&offset=0&postcode=9000&searchInTitleAndDescription=true&sortBy=SORT_INDEX&sortOrder=DECREASING&viewOptions=gallery-view").text
        source = json.loads(source)
        listings = source["listings"]
        blocklist_file = open(os.path.join(path, "blocklist.txt"), "r")
        blocklist_lines = blocklist_file.read().splitlines()
        # Make a dictionary with the advert name as key and the URL as value
        for listing in listings:
            listing = listing
            blocked = False
            # Removes findings that are in the blocklist if there are any items in the blocklist
            if len(blocklist_lines) > 3:
                for line in blocklist_lines:
                    if line[0] != "#" and line.lower() in str(listing).lower():
                        blocked = True
                        print("LISTING BLOCKED BECAUSE OF BLOCKLIST WORD: " + line.lower())
                if not blocked:
                    advertDetails = listing
                    advertURL = listing["vipUrl"].encode('utf-8')
                    foundListingsDictionary[json.dumps(advertDetails)] = advertURL
            # If there are no items in the blocklist:
            else:
                advertDetails = listing
                advertURL = listing["vipUrl"].encode('utf-8')
                foundListingsDictionary[json.dumps(advertDetails)] = advertURL

        newListingsDictionary = {}
        # Reads all the previous found listings
        fileOutput = open(os.path.join(path, "output.txt"), "r+", encoding='utf-8')
        fileURLs = open(os.path.join(path, "URLs.txt"), "a+", encoding='utf-8')
        previousListings = fileOutput.read().splitlines()
        # Check if it is the first time the application is run
        first_install = bool(os.path.getsize(os.path.join(path, "output.txt")) == 0)
        # Checks if the found listings are new listings that haven't been found yet
        for key in foundListingsDictionary:
            if foundListingsDictionary[key].decode('utf-8') not in previousListings:
                print("NEW LISTING: " + json.loads(key)["title"])
                fileOutput.write(foundListingsDictionary[key].decode('utf-8') + "\n")
                fileURLs.write(foundListingsDictionary[key].decode('utf-8') + "\n")
                newListingsDictionary[key] = foundListingsDictionary[key]
        fileOutput.close()
        fileURLs.close()
        # Displays a notification if there are new listings
        if len(newListingsDictionary) > 0 and not first_install:
            if len(newListingsDictionary) > 1:
                print("multiple new listings")
                if show_notification:
                    send_notification("CamAlert", "Multiple new listings")
            # There's 1 new listing
            # Show the name of the listing in the notification + the price
            else:
                print("1 new listing")
                if show_notification:
                    priceType = json.loads(list(newListingsDictionary.keys())[0])["priceInfo"]["priceType"]
                    price = None
                    if priceType == "FIXED" or priceType == "MIN_BID":
                        priceCents = str(json.loads(list(newListingsDictionary.keys())[0])["priceInfo"]["priceCents"])
                        if priceCents[-2::] == "00":
                            price = "€" + priceCents[:-2]
                        else:
                            price = "€" + priceCents[:-2] + "," + priceCents[-2::]
                    elif priceType == "SEE_DESCRIPTION":
                        price = "see description"
                    elif priceType == "RESERVERD":
                        price = "reserved"
                    elif priceType == "NOTK":
                        price = "to be agreed upon"
                    elif priceType == "FAST_BID":
                        price = "bid"
                    send_notification("CamAlert", json.loads(list(newListingsDictionary.keys())[0])["title"] + "\n" + "Price: " + price)
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
    data = file.read().splitlines()
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
