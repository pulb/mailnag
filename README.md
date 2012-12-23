# Mailnag
A mail notification daemon for GNOME 3.  
https://github.com/pulb/mailnag

Mailnag checks POP3 and IMAP servers for new mail.  
When it finds new messsages, it creates a GNOME-Shell notification   
that mentions sender and subject.

__This project needs contributors!__  
[Code](https://github.com/pulb/mailnag)  
[Bugtracker](https://github.com/pulb/mailnag/issues)  
[Translations](https://translations.launchpad.net/mailnag)  
[Wiki](https://github.com/pulb/mailnag/wiki) 

## Installation

### Ubuntu
Mailnag has an official [Ubuntu PPA](https://launchpad.net/~pulb/+archive/mailnag).  
Issue the following commands in a terminal to enable the PPA and install Mailnag.  

    sudo add-apt-repository ppa:pulb/mailnag
    sudo apt-get update
    sudo apt-get install mailnag

As of Ubuntu 13.04 (Raring), Mailnag is also available in the official repos.  
Run `sudo apt-get install mailnag` in a terminal to install it.

### Debian
Mailnag is currently available in Debian unstable.  
Run `sudo apt-get install mailnag` in a terminal to install it.

### Fedora
As of Fedora 17, Mailnag is available in the official Fedora repos.  
Just run `yum install mailnag` (as root) in a terminal to install the package.

### Arch Linux
Mailnag is available in Arch's user community repository [AUR](https://aur.archlinux.org/packages.php?ID=49581).  
Please either run `yaourt -S mailnag` or `packer -S mailnag` (as root) to install the package.

### Generic Tarballs
Distribution independent tarball releases are available [here](https://launchpad.net/mailnag/trunk/mailnag).  
Just run `./setup.py install` (as root) to install Mailnag,  
though make sure the requirements stated below are met.

###### Requirements
* python2 (python3 won't work!)
* pygobject
* gir-notify
* gir-gstreamer
* gir-glib-2.0
* gir-gnomekeyring-1.0
* python-httplib2
* python-dbus
* pyxdg
* gettext


## Configuration
Run `mailnag_config` to setup Mailnag.  
Closing the configuration window will start Mailnag automatically.

### Default Mail Client
Clicking a mail notification popup will open the default mail client specified in `System Settings -> System Info -> Default Applications`.  
If you're a webmail (e.g. gmail) user and want your account to be launched in a browser, please install a tool like [gnome-gmail](http://gnome-gmail.sourceforge.net).

### Permanent Notifications
GNOME-Shell notifications are visible for a few seconds only before they vanish in GNOME's hidden messaging tray.  
If you like to have a permanently visible notification counter in your top panel, you probably want to install [this](https://github.com/pulb/shell-message-notifier) GNOME-Shell extension.

## Screenshots
![Screenshot](http://www.shockshit.net/mailnag/screenshots/mailnag_flyer.png)
