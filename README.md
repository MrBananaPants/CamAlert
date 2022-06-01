# CamAlert
A Python 3 app that sends a notification if there's a new analog camera available on 2dehands (the Ebay of Belgium).
The app runs in the background on macOS and sends a system notification if it sees a new deal is available.
Beautiful Soup is used as HTML parser and [rumps](https://github.com/jaredks/rumps) is used to make the status bar app.

<div align="left">
    <img src="media/Screenshot menu bar.png" height="125"/>
     <img src="media/Screenshot notification.png" height="125"/>
</div>

# Features
- Background check for new listings every 60 seconds
- Sends system notification with listing title if it finds a new listing
- Clicking the notification will open all new listings
- Status bar icon with following options:
  - Open all new listings in the default browser
  - Clear all new listings (in case you haven't used the app in a while and don't want it to open 50+ Chrome tabs)
  - Manual check for new listings
  - Reset
  - Quit the application

# What's not implemented yet
- ~~Manually check for new listings~~ [02a760c](https://github.com/MrBananaPants/CamAlert/commit/02a760c6cb26211a4b548f1a266e51d88d1e7157)
- ~~Manual check should send notification if there are listings that haven’t been opened yet~~ [02a760c](https://github.com/MrBananaPants/CamAlert/commit/02a760c6cb26211a4b548f1a266e51d88d1e7157)
- ~~First time opening app should not open new listings / send notification and can show the user an alert with more info about the app~~ [1f6b5bf](https://github.com/MrBananaPants/CamAlert/commit/1f6b5bf89a52b68d4af816b65a2229547c36989a)
- Option to display icon in menubar instead of text (create a settings json file)
- ~~Try to use the [rumps notification system](https://rumps.readthedocs.io/en/latest/notification.html)~~ [1f6b5bf](https://github.com/MrBananaPants/CamAlert/commit/1f6b5bf89a52b68d4af816b65a2229547c36989a)
- ~~A reset button (in case of problems or bugs)~~ [ddf2bb6](https://github.com/MrBananaPants/CamAlert/commit/ddf2bb6baadc0fd68a957f28067bc1f3ae329480)

# Requirements to build
You need `py2app` to compile the app yourself.

Use `pip install -U py2app` to install it.

From the root of the project folder, run `python setup.py py2app -A` in the terminal to compile the app in Alias mode. The app is ready to open and test in the `dist` folder.

If everything works fine, and you want to create a stand-alone version, you have to remove the build and dist folder (`rm -rf build dist`). Then run `python setup.py py2app` to build the app. The stand-alone build is available in the `dist` folder.
