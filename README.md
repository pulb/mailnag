# Mailnag
A mail notification daemon for GNOME 3.  
https://github.com/pulb/mailnag

Mailnag is a fork of the Popper mail notifier (http://launchpad.net/popper).  
What Popper is to Ubuntu's Unity, Mailnag is to GNOME-Shell.

__This project needs contributors!__  
[Bugtracker](https://github.com/pulb/mailnag/issues)  
[Translations](https://translations.launchpad.net/mailnag)  
[Wiki](https://github.com/pulb/mailnag/wiki) 
***
## Installation

### Unofficial Packages
* [Ubuntu](https://launchpad.net/~webupd8team/+archive/gnome3)
* [Arch Linux](https://aur.archlinux.org/packages.php?ID=49581)

### Generic Tarballs
Distribution independent tarball releases are available [here](https://github.com/pulb/mailnag/downloads).  
To generate locales run `./gen_locales`.  
Your language is not available? Don't hesitate - head over to https://translations.launchpad.net/mailnag  
and translate Mailnag into your language!

###### Requirements
    python2 (python3 won't work!)
    pygobject-3
    gir-notify
    gir-gstreamer
    gir-glib-2.0
    python-httplib2
    python2-gnomekeyring
    pyxdg
    gettext

***
## Configuration
Run `mailnag_config` to setup Mailnag.  
Closing the configuration window will start mailnag automatically.

### Default Mail Client
Clicking a mail notification popup will open the default mail client specified in `System Settings -> System Info -> Default Applications`.  
If you're a webmail (e.g. gmail) user and want your account to be launched in a browser, please install a tool like [gnome-gmail](http://gnome-gmail.sourceforge.net).

### Permanent Notifications
GNOME-Shell notifications are visible for a few seconds only before they vanish in GNOME's hidden messaging tray.  
If you like to have a permanently visible notification counter in your top panel, you probably want to install [this](https://github.com/pulb/shell-message-notifier) GNOME-Shell extension.
***
## Screenshots
![Screenshot](http://www.shockshit.net/mailnag/screenshots/mailnag_flyer.png)
