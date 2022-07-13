import http.client as httplib
import json
import os
import subprocess
import threading
import time
import urllib.request
from pathlib import Path

import requests
import rumps

path = os.path.join(os.getenv("HOME"), "CamAlert")
version = "0.4.0"


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
        if len(lines) > 10:
            if rumps.alert(title="CamAlert", message=f'{len(lines)} tabs will be opened. Do you want to continue?', ok=None, cancel=True) == 1:
                for line in lines:
                    command = "open '" + baseURL + line + "'"
                    os.popen(command)
                    # Clear the URLs.txt file when it's done (so the same listings won't be opened next time)
                    open(os.path.join(path, "URLs.txt"), 'w').close()
            # User pressed cancel on alert
            else:
                if rumps.alert(title="CamAlert", message=f'Open only 10 most recent instead of all {len(lines)} listings?', ok=None, cancel=True) == 1:
                    for i in range(0, 10):
                        command = "open '" + baseURL + lines[i] + "'"
                        os.popen(command)
                        # Clear the URLs.txt file when it's done (so the same listings won't be opened next time)
                        open(os.path.join(path, "URLs.txt"), 'w').close()
        else:
            for line in lines:
                command = "open '" + baseURL + line + "'"
                os.popen(command)
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


def get_listings():
    number_of_listings = 100
    source = requests.get(
        f"https://www.2dehands.be/lrp/api/search?attributesByKey\\[\\]=Language%3Aall-languages&l1CategoryId=31&l2CategoryId=480&limit={number_of_listings}&offset=0&postcode=9000&searchInTitleAndDescription=true&sortBy=SORT_INDEX&sortOrder=DECREASING&viewOptions=gallery-view").text
    print(str(len(source)))
    if len(source) == 161:
        print("BAD REQUEST")
        rumps.alert(title="CamAlert",
                    message="You've made too many update request. Try again later. The app will close now.", ok=None, cancel=None)
        # Get the pid of the CamAlert app
        pid = os.popen("ps -ax | grep CamAlert | awk '{print $1}' | head -n 1").read()
        # Kill the app
        os.system(f'kill {pid}')
    else:
        source = json.loads(source)
        return source["listings"]


def blocklist_filter(listings):
    not_blocked_listings = {}
    blocklist_items = []
    # Get the blocklist items
    with open(os.path.join(path, "blocklist.txt"), "r") as blocklist_file:
        for i in range(3):
            next(blocklist_file)
        for line in blocklist_file:
            blocklist_items.append(line.rstrip().lower())
    # Make a dictionary with the advert name as key and the URL as value
    for listing in listings:
        for blocklist_item in blocklist_items:
            # Removes findings that are in the blocklist if there are any items in the blocklist
            if blocklist_item not in str(listing).lower():
                listing_details = listing
                advert_url = listing["vipUrl"].encode('utf-8')
                not_blocked_listings[json.dumps(listing_details)] = advert_url
            else:
                print(f"BLOCKED LISTING ({blocklist_item}): {listing['title']}")
    return not_blocked_listings


def new_listings(listings):
    new_listings_dictionary = {}
    # Reads all the previous found listings
    file_output = open(os.path.join(path, "output.txt"), "r+", encoding='utf-8')
    file_urls = open(os.path.join(path, "URLs.txt"), "a+", encoding='utf-8')
    previous_listings = set(file_output.read().splitlines())
    # Checks if the found listings are new listings that haven't been found yet
    for key in listings:
        if listings[key].decode('utf-8') not in previous_listings:
            print("NEW LISTING: " + json.loads(key)["title"])
            file_output.write(listings[key].decode('utf-8') + "\n")
            file_urls.write(listings[key].decode('utf-8') + "\n")
            new_listings_dictionary[key] = listings[key]
    file_output.close()
    file_urls.close()
    return new_listings_dictionary


def update_notification(dictionary):
    # Displays a notification if there are new listings
    if len(dictionary) > 0:
        # There are multiple new listings
        if len(dictionary) > 1:
            print("multiple new listings")
            send_notification("CamAlert", "Multiple new listings")
        # There's 1 new listing
        # Show the name of the listing in the notification + the price
        else:
            print("1 new listing")
            price_type = json.loads(list(dictionary.keys())[0])["priceInfo"]["priceType"]
            price = None
            if price_type == "FIXED" or price_type == "MIN_BID":
                price_cents = str(json.loads(list(dictionary.keys())[0])["priceInfo"]["priceCents"])
                if price_cents[-2::] == "00":
                    price = "€" + price_cents[:-2]
                else:
                    price = "€" + price_cents[:-2] + "," + price_cents[-2::]
            elif price_type == "SEE_DESCRIPTION":
                price = "see description"
            elif price_type == "RESERVERD":
                price = "reserved"
            elif price_type == "NOTK":
                price = "to be agreed upon"
            elif price_type == "FAST_BID":
                price = "bid"
            send_notification("CamAlert", json.loads(list(dictionary.keys())[0])["title"] + "\n" + "Price: " + price)
    # There are no new listings
    else:
        print("NO NEW LISTINGS FOUND")


# Update the results to check for new listings
def update(show_notification=True):
    print("UPDATING RESULTS...")
    if check_connection():
        first_install = bool(os.path.getsize(os.path.join(path, "output.txt")) == 0)
        listings = get_listings()
        found_listings_dictionary = blocklist_filter(listings)
        new_listings_dictionary = new_listings(found_listings_dictionary)
        if show_notification and not first_install:
            update_notification(new_listings_dictionary)
        elif first_install:
            # It's the first install of the app, display an alert
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


def check_updates():
    print("CHECKING FOR UPDATES")
    tag = os.popen('curl -sL https://api.github.com/repos/MrBananaPants/CamAlert/releases/latest').read()
    tag = json.loads(tag)
    latest_version = int(str(tag["tag_name"]).lstrip('0').replace(".", ""))
    current_version = int(str(version).lstrip('0').replace(".", ""))

    if latest_version > current_version:
        if rumps.alert(title="CamAlert", message=f'A new version is available. Do you want to download it?', ok=None, cancel=True) == 1:
            urllib.request.urlretrieve(tag["assets"][0]["browser_download_url"], str(os.path.join(os.getenv("HOME"), "Downloads/CamAlert.dmg")))
            rumps.alert(title="CamAlert", message="The newest version has been downloaded to the Downloads folder", ok=None, cancel=None)
    else:
        rumps.alert(title="CamAlert", message="You already have the newest version installed.", ok=None, cancel=None)


def about():
    rumps.alert(title="CamAlert", message=f"Developed by Joran Vancoillie\nversion: {version}", ok=None, cancel=None)


# Run update function every 60 seconds
def every(delay):
    next_time = time.time() + delay
    while True:
        time.sleep(max(0, next_time - time.time()))
        update()
        next_time += (time.time() - next_time) // delay * delay + delay


class StatusBar(rumps.App):
    def __init__(self):
        super(StatusBar, self).__init__("CamAlert")
        self.menu = ["Open new listings", "Clear new listings", None, "Manual update", None, ["Settings", ["Blocklist", "Reset", "Check for updates", "About"]]]

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

    @rumps.clicked("Settings", "Check for updates")
    def reset(self, _):
        check_updates()

    @rumps.clicked("Settings", "About")
    def reset(self, _):
        about()

    @rumps.notifications
    def notifications(self, _):  # function that reacts to incoming notification dicts
        open_listings()


if __name__ == '__main__':
    # Start the loop (with 60 seconds interval)
    threading.Thread(target=lambda: every(60)).start()
    # Do an initial check for new listings when the app starts and start the menu bar app
    check_files()
    update()
    StatusBar().run()
