# CamAlert
A Python 3 app that sends a notification if there's a new analog camera available on 2dehands (the Ebay of Belgium).
The app runs in the background on macOS and sends a system notification if it sees a new deal is available.
Beautiful Soup is used as HTML parser and [rumps](https://github.com/jaredks/rumps) is used to make the status bar app and send the notifications.

<div align="left">
    <img src="media/Screenshot menu bar1.png" height="125"/>
    <img src="media/Screenshot menu bar2.png" height="125"/>
    <img src="media/Screenshot notification.png" height="125"/>
</div>

In the future when the app is complete without bugs, the app might become universal for all types of listings (so not just for analog cameras). Users will have to choice to use their own category of listings they want notifications for. The app will most likely also change names when this happens.
# Features
- Background check for new listings every 60 seconds
- Sends system notification with listing title if it finds a new listing
- Clicking the notification will open all new listings
- Status bar icon with following options:
  - Open all new listings in the default browser
  - Clear all new listings (in case you haven't used the app in a while and don't want it to open 50+ Chrome tabs)
  - Manual check for new listings
  - Blocklist to block certain words or sellers
  - Reset
  - Quit the application

# Requirements to build
You need `py2app` to compile the app yourself.

~~Use `pip install -U py2app` to install it.~~

Important: you need the latest version of rumps which is `0.4.0`. However, this build is not yet available if you use `pip install -U py2app`.
To install the latest version, follow the install instructions [here](https://github.com/jaredks/rumps#installation:~:text=Or%20from%20source,system%2Dwide%20location.)

From the root of the project folder, run `python setup.py py2app -A` in the terminal to compile the app in Alias mode. The app is ready to open and test in the `dist` folder.

If everything works fine, and you want to create a stand-alone version, you have to remove the build and dist folder (`rm -rf build dist`). Then run `python setup.py py2app` to build the app. The stand-alone build is available in the `dist` folder.
