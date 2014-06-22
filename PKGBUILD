# Maintainer: Patrick Ulbrich <zulu99 at gmx . net>
# Contributor: rasmus <rasmus . pank at gmail . com>

pkgname=mailnag
pkgver=0.9.91
pkgrel=1
pkgdesc="An extendable mail notification daemon"
arch=('any')
url="https://github.com/pulb/mailnag"
license=('GPL')
depends=('python2' 'python2-gobject' 'python2-httplib2'
        'libgnome-keyring' 'gnome-keyring' 'python2-xdg'
        'python2-dbus' 'libnotify' 'gstreamer0.10-base-plugins'
        'gtk3' 'gdk-pixbuf2')
optdepends=('mailnag-gnome-shell: for a tighter GNOME 3 integration')
makedepends=('gettext')
source=('https://github.com/pulb/mailnag/archive/0.9.91-testing.tar.gz')
md5sums=('0bcc4b28d1554f05b3f52718d208fc79')
install='mailnag.install'

package() {
  cd "${srcdir}/${pkgname}-${pkgver}-testing"
  python2 setup.py install --root=${pkgdir}
  install -D -m644 LICENSE "${pkgdir}/usr/share/licenses/${pkgname}/LICENSE"
}
