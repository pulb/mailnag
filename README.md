# Mailnag
An extendable mail notification daemon.  
https://github.com/pulb/mailnag

Mailnag checks POP3 and IMAP servers for new mail.  
When it finds new messsages, it creates a notification   
that mentions sender and subject.

__This project needs contributors!__  
[Code](https://github.com/pulb/mailnag)  
[Bugtracker](https://github.com/pulb/mailnag/issues)  
[Translations](https://translations.launchpad.net/mailnag)  
[Wiki](https://github.com/pulb/mailnag/wiki) 

###### Requirements
* python2 (python3 won't work!)
* pygobject
* gir-notify (>= 0.7.6)
* gir-gstreamer
* gir-glib-2.0
* gir-gnomekeyring-1.0
* python-httplib2
* python-dbus
* pyxdg
* gettext


## Configuration
Run `mailnag-config` to setup Mailnag.  
Closing the configuration window will start Mailnag automatically.

### Default Mail Client
Clicking a mail notification popup will open the default mail client specified in `System Settings -> System Info -> Default Applications`.  
If you're a webmail (e.g. gmail) user and want your account to be launched in a browser, please install a tool like [gnome-gmail](http://gnome-gmail.sourceforge.net).

### Desktop integration
By default, Mailnag emits libnotify notifications, which work fine on most desktop environments  
but are visible for a few seconds only. If you like to have a tighter desktop integration  
(e.g. a permanently visible indicator in your top panel) you have to install an appropriate  
extension/plugin for your desktop shell. Currently the following desktops shells are supported:  
* GNOME-Shell [GNOME-Shell extension](https://github.com/pulb/mailnag-gnome-shell)  
* Ubuntu Unity [MessagingMenu plugin](#) (TBD, help is very appreciated!)

## Screenshots
TODO
