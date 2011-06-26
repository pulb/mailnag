# Mailnag
A mail notification daemon for GNOME 3  
https://github.com/pulb/mailnag

Mailnag is a fork of the Popper mail notifier (http://launchpad.net/popper).    
What Popper is to Ubuntu's Unity (messaging menu), Mailnag is to gnome-shell.

Help and Feedback are very appreciated!  
Bugtracker: https://github.com/pulb/mailnag/issue  
Translations: https://translations.launchpad.net/mailnag
***

### Requirements*  
    pyxdg
    notify-python
    python2-gnomekeyring
    python-httplib2
    pygtk2
    pygobject2
    alsa-utils

\* _This list is possibly incomplete. Please let me know if something is missing here._
***

### Configuration

Run `./mailnag_config` to setup Mailnag.    
Closing the configuration window will start mailnag automatically.

To generate locales run `./gen_locales`.    
Your language is not available? Don't hesitate - head over to https://translations.launchpad.net/mailnag and translate Mailnag into your language!
***

### Screenshots

![Screenshot](http://www.shockshit.net/mailnag/screenshots/notification.png "Mail notification")
![Screenshot](http://www.shockshit.net/mailnag/screenshots/config.png "Configuration window")
