# Mailnag
A mail notification daemon for GNOME 3  
https://github.com/pulb/mailnag

Mailnag is a fork of the Popper mail notifier (http://launchpad.net/popper).    
What Popper is to Ubuntu's Unity, Mailnag is to gnome-shell.

__This project needs contributors!__  
Bugtracker: https://github.com/pulb/mailnag/issues  
Translations: https://translations.launchpad.net/mailnag
***

### Requirements*  
    python 2 (python 3 won't work!)
    pygobject-3
    gir-notify
    gir-gstreamer
    python-httplib2
    python2-gnomekeyring
    pyxdg
    gettext

\* _This list is possibly incomplete. Please let me know if something is missing here._
***

### Installation & Configuration
* [Ubuntu](https://launchpad.net/~webupd8team/+archive/gnome3)
* [Arch Linux](https://aur.archlinux.org/packages.php?ID=49581)
* [Generic](https://github.com/pulb/mailnag/downloads)

  Run `./mailnag_config` to setup Mailnag.    
  Closing the configuration window will start mailnag automatically.
  
  To generate locales run `./gen_locales`.    
  Your language is not available? Don't hesitate - head over to https://translations.launchpad.net/mailnag and translate Mailnag into your language!
***

### Screenshots

![Screenshot](http://www.shockshit.net/mailnag/screenshots/notification.png "Mail notification")
![Screenshot](http://www.shockshit.net/mailnag/screenshots/config.png "Configuration window")
